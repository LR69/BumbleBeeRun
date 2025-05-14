import numpy as np
import math
from random import randint
import RPi.GPIO as GPIO
import time
import os
import shutil
import datetime
import sys
import bugcount_utils

import copy
import multiprocessing as mp #MP
import signal #MP
"""
# version du 4/05/25- On part de mitethruV12
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
option = ""
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
elif mode == "calib_en_ligne":
	option = "calib_en_ligne"
	mode = "video"
	p0_flag = False
elif mode == "video" :
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
	if option != "":
		texte+="<li>option : {}</li>\n".format(option)
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
S0 = 23 # capteur barrière IR du côté ruche : pin 16
GPIO.setup(S0, GPIO.IN,pull_up_down=GPIO.PUD_DOWN) 
S1 = 24 # capteur barrière IR du côté extérieur : pin 18
GPIO.setup(S1, GPIO.IN,pull_up_down=GPIO.PUD_DOWN)  

# sorties
PWR_LED = 25 # pin 22 
GPIO.setup(PWR_LED, GPIO.OUT) # commande des leds de puissance (via transistor)
LED_V = 8 # pin 24
GPIO.setup(LED_V, GPIO.OUT) # commande de led verte fonctionnement normal et effacement
LED_J = 7 # pin 26
GPIO.setup(LED_J, GPIO.OUT) # commande de led jaune enregistrement


IMGcount = 0
BPcount = 0
instants_acquisition=[]

instants_cumuls=[]
cumul_NBB_out=[]

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
			bugcount_utils.reinit(option)
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
			for i in range(1,4):
				GPIO.output(LED_V,True) # On  fait clignoter les leds
				GPIO.output(LED_J,True) # On  fait clignoter les leds
				time.sleep(0.2)
				GPIO.output(LED_V,False) # On  fait clignoter les leds
				GPIO.output(LED_J,False) # On  fait clignoter les leds
				time.sleep(0.2)				
			derniere_donnee = datetime.datetime.now() # pour respecter le temps entre 2 données dans le tableau
			REC = False
			debut_video = derniere_donnee
			stop_video = derniere_donnee
			while (GPIO.input(BPma) == 0):
				time.sleep(0.1)# on attend le relâchement du bouton
			num_img = 0
			t_init = datetime.datetime.now()
			

			S0_prev = 0
			S0_prev_img = 0
			S1_prev = 0
			S1_prev_img = 0
			detection = False
			NBB_out = 0
			NBB_out_prev = 0
			t_front = t_init
			while(True):
				# acquisition capteurs
				S0_etat = GPIO.input(S0)
				S1_etat = GPIO.input(S1)
				S0_frontM = (S0_etat == 1) and (S0_prev == 0)
				S1_frontM = (S1_etat == 1) and (S1_prev == 0)

				if not detection:
					if (S1_frontM) and (S0_etat == 1):
						NBB_out += 1 # Un bourdon sort de la ruche
						detection = True
						t_front = datetime.datetime.now()
						GPIO.output(LED_V,True)
					elif (S0_frontM) and (S1_etat == 1):
						NBB_out -= 1 # Un bourdon entre dans la ruche
						detection = True
						t_front = datetime.datetime.now()	
						GPIO.output(LED_J,True)	
						
				maintenant = datetime.datetime.now()
				delta_t = maintenant - t_front
				if detection and (S0_etat == 0) and (S1_etat == 0) and (delta_t.microseconds > 1e5): #> 3*(temps_cycle * 1000)) :
					detection = False # le bourdon est sorti de la zone de détection
					GPIO.output(LED_V,False)
					GPIO.output(LED_J,False)	
							
				# passé = présent
				S0_prev = S0_etat
				S1_prev = S1_etat
				

				# écriture dans tableaux data et sizes
				jobs_temp = jobs.copy() #MP
				if len(jobs)>0: #MP
					for job in jobs_temp: #MP
						if not job.is_alive(): #MP
							jobs.remove(job) #MP
				delta_t = maintenant - derniere_donnee
				if (debug >= 2):
					#print("delta_acariens = {} ; delta_t = {} ; suivis = {}".format(delta_acariens, delta_t, len(objects)))
					os.system('clear')
					print("S0 \t= {} \t prev S0 \t= {}  \t front S0 \t= {} \t \n".format(S0_etat, S0_prev, S0_frontM))   
					print("S1 \t= {} \t prev S1 \t= {}  \t front S1 \t= {} \t \n".format(S1_etat, S1_prev, S1_frontM)) 
					print("NBBout \t={}".format(NBB_out))

				condition = ( delta_t.total_seconds()>=1 ) and ( abs( NBB_out - NBB_out_prev ) > 0 )
				if (condition) and len(jobs) == 0 : #MP
					# On fait une acquisition
					if (debug >= 1):
						print("la date est:",date)
						print("l'heure est :",heure)
						print("Nombre de bourdons comptés : {}".format(NBB_out))

					p1 = mp.Process(target=bugcount_utils.ecrire_ligne, args = (mode,date,heure,NBB_out,t, num_img, dt_frame_min, dt_frame_ms, dt_frame_max) ) #MP
					jobs.append(p1)  #MP
					p1.start()  #MP

					# pour le tracé des graphiques 1 et 2
					instants_cumuls.append(maintenant)
					cumul_NBB_out.append(NBB_out)
					

					
					
					max_pts = 300 # on se limite à 300 points pour le graphique
					if len(instants_cumuls) > max_pts :
						i = randint(1,max_pts) # on enlève un point au hasard
						instants_cumuls.remove(instants_cumuls[i])
						cumul_NBB_out.remove(cumul_NBB_out[i])

						
					p3 = mp.Process(target=bugcount_utils.maj_graphique, args=(instants_cumuls, cumul_NBB_out, "graphique1.png", ))  #MP
					jobs.append(p3)  #MP
					p3.start()  #MP
					derniere_donnee = maintenant # pour calcul du delta_t
					
				# mise à jour de l'état des capteurs	
				if (S0_etat != S0_prev_img) or (S1_etat != S1_prev_img) :
					#print("Mise à jour capteurs : S0 = {} \t Si = {}".format(S0_etat, S1_etat))
					p5 = mp.Process(target=bugcount_utils.maj_capteurs, args=(S0_etat, S1_etat, ))
					jobs.append(p5)
					p5.start()
					S0_prev_img = S0_etat
					S1_prev_img = S1_etat
				# écritures des images dans le serveur 
				delta_t = maintenant - stop_video
				if ((GPIO.input(BPrecord) == 0) and not REC): 
					# APPUI sur le BP d'enregistrement
					debut_video = maintenant
					REC = True
					GPIO.output(LED_J,True)
					#fourmi_mem = fourmi
					instants_cumuls_i=[]
					cumul_NBB_out_i=[]
					S0_i=[]
					S1_i=[]
					if (debug >= 2):
						print("########################## LANCEMENT ACQUISITION VIDEO #########################") #AJTP
				if  (REC and (IMGcount < 10000)):
					dt_i = datetime.datetime.now() - debut_video
					microsec_i = dt_i.seconds*1e6 + dt_i.microseconds
					instants_cumuls_i.append(microsec_i)
					S0_i.append(S0_etat)
					S1_i.append(S1_etat)
					cumul_NBB_out_i.append(NBB_out)
					IMGcount += 1
				delta_t = maintenant - debut_video 
				if (REC and (GPIO.input(BPrecord) == 1)): # on a appuyé sur le BP d'enregistrement, mais maintenant il est relâché
					REC = False
					GPIO.output(LED_J,False)
					p6 = mp.Process(target=bugcount_utils.package_rec, args=(instants_cumuls_i, S0_i, S1_i, cumul_NBB_out_i, )) #MP
					jobs.append(p6)  #MP
					p6.start()  #MP
					fourmi_mem = 0
					IMGcount = 0
					stop_video = maintenant
					if (debug >= 2):
						print("########################## ARRET ACQUISITION VIDEO #########################") #AJTP
				# clear the stream in preparation for the next frame
				#rawCapture.truncate(0)
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
				num_img = 0
			print("Bouton marche relâché")
			GPIO.output(LED_V,True) # On  fait clignoter les leds
			GPIO.output(LED_J,True) # On  fait clignoter les leds
			time.sleep(2)
			GPIO.output(LED_V,False) # On  fait clignoter les leds
			GPIO.output(LED_J,False) # On  fait clignoter les leds
	time.sleep(0.1) #indispensable pour le respect des temps des boutons
GPIO.cleanup() # indispensable ?? try / Finally ?
