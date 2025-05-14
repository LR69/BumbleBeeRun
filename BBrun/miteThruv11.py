from picamera.array import PiRGBArray
from picamera import PiCamera
import numpy as np
import math
from random import randint
import cv2
import RPi.GPIO as GPIO
import time
import os
import shutil
import datetime
import sys
import bugcount_utils
import img_count_utils as imcount
from mitestracker import MitesTracker
import copy
import multiprocessing as mp #MP

"""
# version du 19/01/20- Avertissement fichier image Full
# version du 24/02/20 - ajout alerte fourmi
 version du 11/06/20 :
	- maj des graphiques facultative
	- main() en nice < 0
	- p1 à p6 en nice > 0
 """

os.nice(-5) # le programme principal est agressif

#initialisation de l'interface images
shutil.copyfile("/var/www/html/pre_index_images_ini.html", "/var/www/html/pre_index_images.html")

#Vérification de la conformité de la commande passée :
msg_gal = "ERREUR : rappel de la commande miteThru : python3 miteThruVi.py -Fe f -mode mode [s] [d] [i]"
if len(sys.argv) < 5:
	print(msg_gal)
	print("Le nombre d'argument doit être >= 3")
	sys.exit(1)

mode = sys.argv[4]
if mode == "debug" or mode == "normal":
	if len(sys.argv) != 6:
		print(msg_gal)
		print("mode \"{}\", il faut un seul argument après le mode".format(mode))
		sys.exit(1)
	try:
		s=int(sys.argv[5])
	except ValueError:
		print(msg_gal)
		print("L'argument après le mode doit être un nombre entier")
		sys.exit(1)
elif mode == "video":
	if len(sys.argv) != 8:
		print(msg_gal)
		print("mode \"{}\", il faut 3 arguments après le mode".format(mode))
		sys.exit(1)
	try:
		s=int(sys.argv[5])
		s=int(sys.argv[6])
		s=int(sys.argv[7]) 
	except ValueError:
		print(msg_gal)
		print("L'argument après le mode doit être un nombre entier")
		sys.exit(1)
else:
	if mode != "calib":
		print(msg_gal)
		print("Le mode \"{}\" n'est pas reconnu".format(mode))
		sys.exit(1)

# gestion des modes 
seuil_video = 9999
duree_video = 1
intervalle_min_video = 99999
debug = 0
if (mode == "video"):
	seuil_video = int(sys.argv[5]) # nombre d'acariens suivis déclenchant une acquisition video
	duree_video = int(sys.argv[6]) # duree de l'acquisition vidéo (en secondes)
	intervalle_min_video = int(sys.argv[7]) # intervalle minimum entre deux acquisitions videos (en secondes)
	texte="<h1>Aquisition automatique de vidéos</h1>\n <ul>\n"
	texte+="<li>nombre d'acariens suivis déclenchant une acquisition video : {}</li>\n".format(seuil_video)
	texte+="<li>duree de l'acquisition vidéo (en secondes) : {}</li>\n".format(duree_video)
	texte+="<li>intervalle minimum entre deux acquisitions videos (en secondes):{}</li>\n</ul>\n".format(intervalle_min_video)
elif (mode == "normal"):
	texte="<h1>Aquisition automatique de vidéos</h1>\n \n"
	if int(sys.argv[5]) == 0:
		texte+="<p> L'acquisition automatique a été désactivée par l'utilisateur.</p>"
	else:
		texte+="<p> L'acquisition automatique a été désactivée car la taille totale des images sur la carte SD dépasse 1GB. Pensez à faire un Reset.</p>"
elif (mode == "calib"):
	texte="<h1>Aquisition automatique de vidéos</h1>\n \n"
	texte+="<p> Le miteThru est en mode CALIBRATION. L'acquisition est forcée à une image par seconde.</p>"
	texte+="<p> Aucun enregistrement vidéo n'est effecué.</p>"
	texte+="<p> Les données d'aires sont mémorisée dans un fichier \"data.csv\".</p>"
elif (mode == "debug"):
	debug = int(sys.argv[5]) # niveau de nervosité du debug 
	texte="<h1>Aquisition automatique de vidéos</h1>\n \n"
	texte+="<p> Le miteThru est en mode Debug. avec un niveau de verbosité de {}</p>".format(debug)
# Gestion de la fréquence d'échantillonnage
try:
	Fe = int(sys.argv[2]) # fréquence d'échantillonage
except ValueError:
	print(msg_gal)
	print("La frequence d'échantillonnage doit être un nombre entier")
	sys.exit(1)

with open('/var/www/html/pre_index_images.html','a') as preamb:
	if Fe == 0 :
		texte+="<p> La fréquence d'échantillonnage n'est pas limitée</p>"
	else:
		texte+="<p> La fréquence d'échantillonnage maximale est fixée à {} images par secondes</p>".format(Fe)
	texte+="<p></p>"
	texte+="<h1>Images mémorisées </h1>\n"
	texte+="\t<div align=center>\n"
	texte+="\t\t<table>\n"
	preamb.write(texte)
	print(texte) #pour le log
if Fe == 0:
	Fe = 99999 # pas de limitation
temps_cycle = 1000/Fe #temps de cycle minimum


# pour le mode debug 8 = forçage de reset 
bypass_reset = False
if debug == 8:
	bypass_reset = True
	with open("stop_normal",'w') as mon_fichier:
		mon_fichier.write("forçage de reset en mode debug")
		

# gestion du redémarrage après coupure de courant
if os.path.exists("stop_normal"):
	bypass = False
else:
	bypass = True

# pour le mode debug 9 = forçage de lancement
if debug == 9:
	bypass = True

# initialisation des pins du rpi
GPIO.setmode(GPIO.BCM)
GPIO.setwarnings(False)

# entrées
BPrecord = 16 # Bouton enregistrement : pin 36
GPIO.setup(BPrecord, GPIO.IN,pull_up_down=GPIO.PUD_UP) 
BPma = 20  # bouton marche arrêt : pin 38
GPIO.setup(BPma, GPIO.IN,pull_up_down=GPIO.PUD_UP)  
BPreset = 21 # bouton de reset : pin 40
GPIO.setup(BPreset, GPIO.IN,pull_up_down=GPIO.PUD_UP)  

# sorties
PWR_LED = 25 # pin 22 
GPIO.setup(PWR_LED, GPIO.OUT) # commande des leds de puissance (via transistor)
LED_V = 8 # pin 24
GPIO.setup(LED_V, GPIO.OUT) # commande de led verte fonctionnement normal et effacement
LED_J = 7 # pin 26
GPIO.setup(LED_J, GPIO.OUT) # commande de led jaune enregistrement

#https://docs.opencv.org/3.3.0/d3/db4/tutorial_py_watershed.html
# initialize the camera and grab a reference to the raw camera capture
camera = PiCamera()
camera.resolution = (704, 528) #(704, 528), (1024,768) ou (3200, 2404)
camera.framerate = 24
camera.brightness = 70
camera.contrast = 50
rawCapture = PiRGBArray(camera, size=(704, 528)) # à changer aussi !
time.sleep(2)
(w, h) = camera.resolution




# dimension du cercle frontière (version commune)
center = (int(w / 2), int(h / 2))
rayon = int(0.35*h)
trackW = int(0.25*h) # largeur de la zone de traçage
countW = int(0.05*h)  # largeur de la zone de comptage
if (debug >=1 or mode == "calib"):
	print("largeur de la zone de suivi : {}".format(trackW))
	print("largeur de la zone de comptage : {}".format(countW))

#initialisation mite tracker

mt = MitesTracker((w, h), (center, rayon), trackW, countW, 50)
mt_old = copy.copy(mt)
IMGcount = 0
BPcount = 0
instants_acquisition=[]
taux_franchissement_montee=[]
taux_franchissement_descente=[]
instants_cumuls=[]
cumul_ast_montee=[]
cumul_dg_nym_montee=[]
cumul_dg_adu_montee=[]
cumul_ast_descente=[]
cumul_dg_nym_descente=[]
cumul_dg_adu_descente=[]
jobs=[] #MP
dt_frame_ms = 0 # temps d'acquisition et de traitement d'une image
dt_frame_min = 500 # valeur mini de dt_frame_ms observée
dt_frame_max = 0 # valeur maxi de dt_frame_ms observée
while(True): 
	maintenant = datetime.datetime.now()
	date = maintenant.strftime('%Y-%m-%d')
	heure = maintenant.strftime('%H:%M:%S')
	if (GPIO.input(BPreset) == 0)and (GPIO.input(BPma) == 1): # on APPUIE sur le BP de reset
		BPcount += 1
		GPIO.output(LED_V,True)
		print("appui sur BPreset n=",BPcount)
		if ((BPcount > 20) and (BPcount<40)): # on est resté appuyé pendant 2s
			if (BPcount%2) == 0 :
				GPIO.output(LED_V,True) 
			else:
				GPIO.output(LED_V,False)
		if (BPcount >= 40): # on est resté appuyé trop longtemps
			GPIO.output(LED_V,False)
	if (GPIO.input(BPreset) == 1) and (GPIO.input(BPma) == 1): # on N'APPUIE PAS sur le BP de reset
		if ((BPcount > 20) and (BPcount<40) or bypass_reset): # on a relâché pendant le clignotement
			# initialisation des fichiers : A RENDRE CONDITIONNEL PAR APPUI GPIO
			print("{} {} : EFFACEMENT DONNEES".format(date,heure))
			GPIO.output(LED_V,True)
			bugcount_utils.reinit()
			IMGcount = 0
			bypass_reset = False
			time.sleep(1)
		BPcount =0 
		# Extinction LEDs
		GPIO.output(LED_V,False)
		GPIO.output(PWR_LED,False) 

	if ((GPIO.input(BPma) == 0) and (GPIO.input(BPreset) == 1) or bypass): # on APPUIE sur le BP de marche et pas sur Reset
		print("appui sur BPmarche n=",BPcount)
		BPcount += 1
		if ((BPcount>10) or bypass): #on lance le démarrage du programme
			fichier_flag = "stop_normal"
			if os.path.exists(fichier_flag):
				os.remove(fichier_flag)
			print("{} {} : On lance le programme principal de vision".format(date,heure))
			GPIO.output(PWR_LED,True) # On allume les LEDS de puissance
			derniere_donnee = datetime.datetime.now() # pour respecter le temps entre 2 données dans le tableau
			REC = False
			debut_video = derniere_donnee
			stop_video = derniere_donnee
			while (GPIO.input(BPma) == 0):
				time.sleep(0.1)# on attend le relâchement du bouton
			num_img = 0
			t_init = datetime.datetime.now()
			for frame in camera.capture_continuous(rawCapture, format="bgr", use_video_port=True):
				GPIO.output(LED_V,True)
				#acquisition image
				capt = frame.array
				img=capt.copy()
				GPIO.output(LED_V,False) # on a pris une image
				# creation du masque
				mask = np.zeros((h,w),np.uint8)
				cv2.circle(mask,center,int(rayon),(255,255,255),trackW)

				# traitement 
				cercles, fourmi = imcount.bugcount(img, mask, mt.AREA_MIN_ACA, mt.AREA_MAX_ACA, mode)
				#print(cercles)
				if num_img < 20 :
					cercles=[]
					num_img += 1
				objects = mt.update(cercles) 
				delta_acariens = mt - mt_old
				# loop over the tracked objects
				for (objectID, centroid) in objects.items():
					# draw both the ID of the object and the centroid of the
					# object on the output frame
					if (mt.etat[objectID] == 'IN') :
						couleur_ID = (0, 255, 0)
					else:
						couleur_ID = (0, 0, 0)
					text = "ID {}".format(objectID)
					cv2.putText(img, text, (centroid[0] - 10, centroid[1] - 10),
						cv2.FONT_HERSHEY_SIMPLEX, 0.4, couleur_ID, 1)

					if mt.nature[objectID] == 'ASTIGMATA' :
						couleur_cercle = mt.couleur_ASTIGMATA 
					elif mt.nature[objectID] == 'DG_NYMPH' :
						couleur_cercle = mt.couleur_DG_NYMPH
					elif mt.nature[objectID] == 'DG_ADULT' :
						couleur_cercle = mt.couleur_DG_ADULT 
					else: 
						couleur_cercle = (255,0,255)
					cv2.circle(img, (centroid[0], centroid[1]), int(math.sqrt(mt.areas[objectID]/math.pi)), couleur_cercle, -1)


				#tracé de la  frontière
				cv2.circle(img,center,int(rayon),(0,0,255),1)
				#tracé de la zone de référencement
				cv2.circle(img,center,int(rayon + trackW/4),(128,128,128),1)
				cv2.circle(img,center,int(rayon  - trackW/4),(128,128,128),1)
				#tracé de la zone de tracking
				cv2.circle(img,center,int(rayon + trackW/2),(96,96,96),1)
				cv2.circle(img,center,int(rayon  - trackW/2),(96,96,96),1)
				# tracé de la zone de comptage
				cv2.circle(img,center,int(rayon  + countW/2),(0,255,0),1)
				cv2.circle(img,center,int(rayon  - countW/2),(0,255,0),1)
				# affichage du nombre d'acariens ayant passé la frontière
				text = "astgm : IN {} OUT {}".format(mt.number_astigmata_IN, mt.number_astigmata_OUT)
				cv2.putText(img, text, (w - 200, 75), cv2.FONT_HERSHEY_SIMPLEX, 0.4, mt.couleur_ASTIGMATA , 2)
				text = "dg_nymph IN {} OUT {}".format(mt.number_dg_nymph_IN, mt.number_dg_nymph_OUT)
				cv2.putText(img, text, (w - 200, 50), cv2.FONT_HERSHEY_SIMPLEX, 0.4, mt.couleur_DG_NYMPH , 2)
				text = "dg_adult_IN {} OUT {}".format(mt.number_dg_adult_IN, mt.number_dg_adult_OUT)
				cv2.putText(img, text, (w - 200, 25), cv2.FONT_HERSHEY_SIMPLEX, 0.4, mt.couleur_DG_ADULT , 2)
				
				# mode étalonnage
				if mode == "calib" :
					text = "ETALONNAGE"
					cv2.putText(img, text, (100, 25), cv2.FONT_HERSHEY_SIMPLEX, 0.4, (0,0,255), 2)
					#cv2.rectangle(img, (int(center_calib[0]-trackW/2), int(center_calib[1] -trackW/2)) , (int(center_calib[0]+trackW/2), int(center_calib[1] +trackW/2)), (255,255,255), 2) 
				# écriture image brute pour affichage
				chemin_image="/var/www/html/images_bugcount/live/image_brute.jpg"
				cv2.imwrite(chemin_image, capt)
				# écriture image traitée pour affichage
				chemin_image="/var/www/html/images_bugcount/live/image_traitee.jpg"
				cv2.imwrite(chemin_image, img)
				
				# écriture dans tableaux data et sizes
				jobs_temp = jobs.copy() #MP
				if len(jobs)>0: #MP
					for job in jobs_temp: #MP
						if not job.is_alive(): #MP
							jobs.remove(job) #MP
				delta_t = maintenant - derniere_donnee
				if (debug >= 2):
					print("delta_acariens = {} ; delta_t = {} ; suivis = {}".format(delta_acariens, delta_t, len(objects)))
				condition_1 = delta_t.total_seconds()>600
				condition_2 = delta_t.total_seconds()>60 and len(objects) > 5
				condition_3 = delta_t.total_seconds()>30 and len(objects) > 30
				condition_4 = delta_t.total_seconds()>10 and len(objects) > 50
				condition_5 = delta_t.total_seconds()>=1 and max(delta_acariens) > 1
				condition_bidon = delta_t.total_seconds()>1 and mode == "calib"
				if (condition_1 or condition_2 or condition_3 or condition_4 or condition_5 or condition_bidon) and len(jobs) == 0 : #MP
					# On fait une acquisition
					if (debug >= 1):
						print("la date est:",date)
						print("l'heure est :",heure)
						print("Nombre d'acariens suivis : {}".format(len(objects)))
						print("Nombre astigmates montés sur le perchoir : {}".format(mt.number_astigmata_IN))
						print("Nombre astigmates descendus du perchoir : {}".format(mt.number_astigmata_OUT))
						print("Nombre dg nymphes montés sur le perchoir : {}".format(mt.number_dg_nymph_IN))
						print("Nombre dg nymphes descendus du perchoir : {}".format(mt.number_dg_nymph_OUT))
						print("Nombre dg adultes montés sur le perchoir : {}".format(mt.number_dg_adult_IN))
						print("Nombre dg adultes descendus du perchoir : {}".format(mt.number_dg_adult_OUT))
					p1 = mp.Process(target=bugcount_utils.ecrire_ligne, args = (mode,date,heure,len(objects),mt.number_astigmata_IN,mt.number_dg_nymph_IN, mt.number_dg_adult_IN, 
						mt.number_astigmata_OUT,mt.number_dg_nymph_OUT, mt.number_dg_adult_OUT, t, num_img, dt_frame_min, dt_frame_ms, dt_frame_max))  #MP
					jobs.append(p1)  #MP
					p1.start()  #MP
					if mode == "calib" :
						aires = [aire for aire in mt.areas.values()]
						IDs = [objectID for objectID in mt.objects.keys()]
						etats = [loc for loc in mt.etat.values()]
						if len(aires) > 0 :
							p2 = mp.Process(target=bugcount_utils.ecrire_aires, args = (date,heure,aires, IDs, etats ))  #MP
							jobs.append(p2)  #MP
							p2.start()  #MP
					# pour le tracé des graphiques 1 et 2
					instants_cumuls.append(maintenant)
					cumul_ast_montee.append(mt.number_astigmata_IN)
					cumul_dg_nym_montee.append(mt.number_dg_nymph_IN)
					cumul_dg_adu_montee.append(mt.number_dg_adult_IN)
					cumul_ast_descente.append(mt.number_astigmata_OUT)
					cumul_dg_nym_descente.append(mt.number_dg_nymph_OUT)
					cumul_dg_adu_descente.append(mt.number_dg_adult_OUT)
					
					
					max_pts = 300 # on se limite à 300 points pour le graphique
					if len(instants_cumuls) > max_pts :
						i = randint(1,max_pts) # on enlève un point au hasard
						instants_cumuls.remove(instants_cumuls[i])
						cumul_ast_montee.remove(cumul_ast_montee[i])
						cumul_dg_nym_montee.remove(cumul_dg_nym_montee[i])
						cumul_dg_adu_montee.remove(cumul_dg_adu_montee[i])
						cumul_ast_descente.remove(cumul_ast_descente[i])
						cumul_dg_nym_descente.remove(cumul_dg_nym_descente[i])
						cumul_dg_adu_descente.remove(cumul_dg_adu_descente[i])
						
					p3 = mp.Process(target=bugcount_utils.maj_graphique, args=(instants_cumuls, cumul_ast_montee, cumul_dg_nym_montee, cumul_dg_adu_montee, "graphique1.png", ))  #MP
					jobs.append(p3)  #MP
					p3.start()  #MP
					p4 = mp.Process(target=bugcount_utils.maj_graphique, args=(instants_cumuls, cumul_ast_descente, cumul_dg_nym_descente, cumul_dg_adu_descente, "graphique2.png", ))  #MP
					jobs.append(p4)  #MP
					p4.start()  #MP
					
					# graphique 3 : taux de franchissement
					instants_acquisition.append(maintenant)
					taux_franchissement_montee.append(60*60*delta_acariens[0]/delta_t.total_seconds())
					taux_franchissement_descente.append(60*60*delta_acariens[1]/delta_t.total_seconds())
					p5 = mp.Process(target=bugcount_utils.maj_graphique3, args=(instants_acquisition,taux_franchissement_montee,taux_franchissement_descente, ))  #MP
					jobs.append(p5)  #MP
					p5.start()  #MP
					derniere_donnee = maintenant # pour calcul du delta_t
					mt_old = copy.copy(mt) # pour calcul du delta_acariens
				# écritures des images dans le serveur 
				delta_t = maintenant - stop_video
				if ((((len(objects) >= seuil_video) or fourmi) and delta_t.total_seconds()>intervalle_min_video and mode == "video" and not REC) or (GPIO.input(BPrecord) == 0)): 
					# seuil vidéo ou fourmi détectée ou APPUI sur le BP d'enregistrement
					debut_video = maintenant
					REC = True
					fourmi_mem = fourmi
					if (debug >= 2):
						print("########################## LANCEMENT ACQUISITION VIDEO #########################") #AJTP
				if  (REC and (IMGcount < 1000)):
					# On enregistre deux images sur le serveur
					# écriture image brute dans le serveur
					GPIO.output(LED_J,True)
					date2 = maintenant.strftime('%Y_%m_%d_')
					heure2 = maintenant.strftime('%Hh%Mm%Ss.%f')
					nom_image_brute = "image_brute_" + date2 + heure2 
					chemin_image="/var/www/html/images_bugcount/images_brutes/"+nom_image_brute + ".jpg"
					cv2.imwrite(chemin_image, capt)
					GPIO.output(LED_J,False)
					#écriture image traitée dans le serveur
					nom_image_traitee = "image_traitee_" + date2 + heure2
					chemin_image="/var/www/html/images_bugcount/images_traitees/"+nom_image_traitee  + ".jpg"
					cv2.imwrite(chemin_image,img)
					IMGcount += 1
				delta_t = maintenant - debut_video 
				if ((((GPIO.input(BPrecord) == 1) and mode != "video") or ((delta_t.total_seconds() > duree_video) and mode == "video")) and (IMGcount > 0)): # on a appuyé sur le BP d'enregistrement, mais maintenant il est relâché
					REC = False
					p6 = mp.Process(target=bugcount_utils.package_images, args=(fourmi_mem, )) #MP
					jobs.append(p6)  #MP
					p6.start()  #MP
					fourmi_mem = 0
					IMGcount = 0
					stop_video = maintenant
					if (debug >= 2):
						print("########################## ARRET ACQUISITION VIDEO #########################") #AJTP
				# clear the stream in preparation for the next frame
				rawCapture.truncate(0)
				if (GPIO.input(BPma) == 0): #on appuie sur le bouton marche
					BPcount = 0
					print("appui sur BPmarche pour sortie de boucle n=",BPcount)
					with open("stop_normal",'w') as mon_fichier:
						mon_fichier.write("stop normal")
					break # on sort de l'acquisition continue
				else:
					num_img += 1 # image suivante
					dt_frame = datetime.datetime.now() - maintenant	 
					dt_frame_ms = round(dt_frame.seconds*1000 + (dt_frame.microseconds/1e3),1) #intervalle de temps en millième de s
					if num_img > 40: # pb de temps de cylcle plus long lors des premiers cycles
						if dt_frame_ms < dt_frame_min and dt_frame_ms > 0:
							dt_frame_min = dt_frame_ms
						if dt_frame_ms > dt_frame_max:
							dt_frame_max = dt_frame_ms
					if (dt_frame_ms <  temps_cycle ): # bridage 
						tempo = (temps_cycle - dt_frame_ms )/1e3 # bridage
						time.sleep(tempo) # bridage à 8 acquisitions par seconde
						dt_frame = datetime.datetime.now() - maintenant	 # bridage 
						dt_frame_ms = round(dt_frame.seconds*1000 + (dt_frame.microseconds/1e3),1) # bridage 
					if debug >= 2 :
						print("Durée d'acquisition : min :{} ms ; actu : {} ms ;  max :{} ms".format(dt_frame_min, dt_frame_ms, dt_frame_max))
					maintenant = datetime.datetime.now()
					t_dt = maintenant - t_init
					t = t_dt.seconds
					date = maintenant.strftime('%Y-%m-%d')
					heure = maintenant.strftime('%H:%M:%S')

			print("{} {} : Sortie de la boucle principale de vision".format(date,heure))
			bypass = False
			while (GPIO.input(BPma) == 0):
				print("on attend le relâchement du bouton marche")
				time.sleep(0.1)# on attend le relâchement du bouton
			print("Bouton marche relâché")
	time.sleep(0.1) #indispensable pour le respect des temps des boutons
GPIO.cleanup() # indispensable ?? try / Finally ?
