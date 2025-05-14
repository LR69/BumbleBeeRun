import datetime
import time
import random
import cv2
import shutil
import os
import re
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.ticker import MaxNLocator
import numpy as np
# version miteThruv9 du 12/1/20 ajout intercalaire
# version miteThruv9b du 26/01/20 data.csv --> hostname.csv
# version miteThruv11 du 15/06/20 processus courtois
# version miteThruv11 du 25/06/20 ajout de l'affichage de la taille du fichier image
# version BBrun du 4/05/25

# variables globales
hostname = os.uname()[1]
nom_fichier_data = hostname + ".csv"
nom_fichier_calib_en_ligne = hostname + "_calib_en_ligne.csv"
COURTOISIE = 10 # pour la fonction os.nice
en_tete = """
	<p></p>
	<h1>Tableau des 100 dernières acquisitions</h1>
		<div class="container-table100">
			<div class="wrap-table100">
				<div class="table100 ver1 m-b-110">
					<div class="table100-head">
						<table>
							<thead>
								<tr class="row100 head">
									<th class="cell100 column1">Date</th>
									<th class="cell100 column2">Heure</th>
									<th class="cell100 column3">NBB_out</th>
								</tr>
							</thead>
						</table>
					</div>

					<div class="table100-body js-pscroll">
						<table>
							<tbody>
"""

def reinit(option) :
# on peut réinitialiser l'enregistrement en supprimant le fichier "data.csv"
# initialisation des fichiers d'interface si nécessaire
	with open("/var/www/html/post_index_ini.html",'r') as fichier:
		post_index = fichier.read()
		post_index2 = re.sub('data.csv', nom_fichier_data, post_index)
		if option == "calib_en_ligne": 
			post_index3 = re.sub('data_calib_en_ligne.csv', nom_fichier_calib_en_ligne, post_index2)
		else: 
			chaine = '<a href="data_calib_en_ligne.csv" class="button">Télécharger les données les données de calibrage en ligne</a>'
			post_index3 = re.sub(chaine, "", post_index2)
	with open("/var/www/html/post_index.html",'w') as fichier:
		fichier.write(post_index3)
	empl_fichier_data = "/var/www/html/" + nom_fichier_data 
	with open(empl_fichier_data , 'w') as fichier:
		#chaine="Date,Heure,Nbre_acariens_Suivis,Montee_Astigmates,Montee_Nymphes,Montee_Adultes,Descente_Astigmates,Descente_Nymphes,Descente_Adultes" +'\n'
		chaine="Date,Heure,Nombre_Bourdons_Sortis" +'\n'
		fichier.write(chaine)
	empl_fichier_calib_en_ligne = "/var/www/html/" + nom_fichier_calib_en_ligne
	with open(empl_fichier_calib_en_ligne , 'w') as fichier:
		chaine="ID,Date,Heure,Nature,Etat,Aire (en pixels ^ 2)" +'\n'
		fichier.write(chaine)
	with open("/var/www/html/aires.csv", 'w') as fichier:
		chaine="Date,Heure,Aires acariens suivis (en pixels ^ 2)" +'\n'
		fichier.write(chaine)
	with open("/var/www/html/IDs.csv", 'w') as fichier:
		chaine="Date,Heure,ID acariens suivis" +'\n'
		fichier.write(chaine)
	with open("/var/www/html/etats.csv", 'w') as fichier:
		chaine="Date,Heure,Etat des acariens" +'\n'
		fichier.write(chaine)

	with open("/var/www/html/corps_index.html", 'w') as mon_fichier:
		chaine=""
		mon_fichier.write(chaine)
	shutil.rmtree("/var/www/html/images_bugcount")
	os.mkdir("/var/www/html/images_bugcount")
	os.mkdir("/var/www/html/images_bugcount/images_brutes")
	os.mkdir("/var/www/html/images_bugcount/images_traitees")
	os.mkdir("/var/www/html/images_bugcount/live")
	
	# RAZ page images
	with open('/var/www/html/pre_index_images.html','r') as preamb:
		preambule=preamb.read()       
	with open('/var/www/html/post_index_images.html','r') as post:
		postscript=post.read()    
	contenu = preambule + " \n" + postscript
	with open("/var/www/html/index_images.html",'w') as index_html:
			index_html.write(contenu)
	ligne ="<tr> </tr> <tr> <td> <hr> </td> <td> <hr>  </td> <td> <hr> </td></tr> <tr>  </tr>\n"
	with open("/var/www/html/images.html",'w') as images_l:
			images_l.write(ligne)
def ecrire_aires(date,heure,aires, IDs, etats):
	os.nice(COURTOISIE) # la maj des données est courtoise
	# mise à jour du fichier d'aires
	with open("/var/www/html/aires.csv",'a') as mon_fichier:
		ligne = date + "," + heure +"," + ",".join(map(str,aires))+ '\n'
		mon_fichier.write(ligne)
	
	# mise à jour du fichier d'identifiants
	with open("/var/www/html/IDs.csv",'a') as mon_fichier:
		ligne = date + "," + heure + "," + ",".join(map(str,IDs))+ '\n'
		mon_fichier.write(ligne)
		
	# mise à jour du fichier d'états IN or OUT
	with open("/var/www/html/etats.csv",'a') as mon_fichier:
		ligne = date + "," + heure + "," + ",".join(map(str,etats))+ '\n'
		mon_fichier.write(ligne)

def ecrire_aire_en_ligne(l_ID, date,heure,l_nature,l_etat,l_aire):
	os.nice(COURTOISIE) # la maj des données est courtoise
	#hostname = os.uname()[1]
	#nom_fichier_calib_en_ligne = hostname + "_calib_en_ligne.csv"
	empl_fichier_calib_en_ligne = "/var/www/html/" + nom_fichier_calib_en_ligne
	# mise à jour du fichier d'aires
	with open(empl_fichier_calib_en_ligne,'a') as mon_fichier:
		ligne = ""
		for ID in l_ID:
			i = l_ID.index(ID)
			ligne += str(ID) + "," + date + "," + heure + "," + l_nature[i] + "," + l_etat[i] + "," + str(l_aire[i]) + '\n'
		mon_fichier.write(ligne)


def ecrire_ligne(mode,date,heure,NBB_out,t, num_img, dt_frame_min, dt_frame_ms, dt_frame_max):  #MP
	os.nice(COURTOISIE) # la maj des données est courtoise         
	# mise à jour du fichier de données
	empl_fichier_data = "/var/www/html/" + nom_fichier_data 
	with open(empl_fichier_data,'a') as mon_fichier:
		chaine = date + "," + heure + "," + \
			str(NBB_out) + '\n'
		mon_fichier.write(chaine)


	# mise à jour de l'interface html
	with open("/var/www/html/corps_index.html", 'r') as mon_fichier:
		lignes = mon_fichier.read().splitlines()
	if len(lignes) >= 100 : # on limite le nombre de lignes à 100
		der = lignes.pop()
	ligne = "<tr class=""row100 body"">" + \
			"<td class=""cell100 column1"">"+ date + "</td>" + \
			"<td class=""cell100 column2"">"+ heure + "</td>" + \
			"<td class=""cell100 column3"">"+ str(NBB_out)+ "</td>" + \
			 "</tr>"
	lignes.insert(0,ligne)
	txt_lignes = "\n".join(lignes) + "\n" 
	with open("/var/www/html/corps_index.html", 'w') as mon_fichier:
		mon_fichier.write(txt_lignes)
	# affichage du nombre de bourdons
	lignes3 = "<h1>Nombre de bourdons qui sont à l'extérieur de la ruche</h1>\n"
	lignes3 +="<h2> NBBout \t = {} </h2>".format(NBB_out)
	
	# affichage de la fréquence d'acquisition
	lignes4 = "<h1>Fréquence d'acquistion</h1>\n"
	if float(t)>0.001:
		vitesse = num_img / float(t)
	else:
		vitesse = 0
	lignes4 += "<table>" 
	if dt_frame_max < 500 :
		lignes4 += " <tr> <td> Durée d'acquisition </td> <td> mini : {:.1f}  ms </td> <td> actuelle : {:.1f}  ms </td> <td> maxi : {:.1f}  ms  </td> </tr>".format(dt_frame_min, dt_frame_ms, dt_frame_max)
	else :
		lignes4 += " <tr> <td> Durée d'acquisition </td> <td> mini : {:.1f}  ms </td> <td> actuelle : {:.1f} ms </td> <td style=""color:Red;""> maxi : <b> {:.1f}  ms </b> </td> </tr>".format(dt_frame_min, dt_frame_ms, dt_frame_max)
	lignes4 += " <tr> <td colspan=""2"" style=""text-align:left""> Fréquence moyenne d'acquisition et de traitement : </td> <td colspan=""2"" style=""text-align:left""> {:.3f} acquisitions / s <td>".format(vitesse)
	#lignes4 += " <tr> <td colspan=""2"" style=""text-align:left""> temps écoulé :{:d}s </td> <td colspan=""2"" style=""text-align:left""> nombre d'images : {:d} images  <td>".format(t, num_img)
	lignes4 += "</table>" 
	
	# lecture des header et footer
	with open('/var/www/html/pre_index.html','r') as preamb:
		preambule=preamb.read()       
	if mode == "calib" : #pour rajouter les boutons permettant de charger les aires et les IDs
		with open('/var/www/html/post_index_calib.html','r') as post:
			postscript=post.read() 
	else:
		with open('/var/www/html/post_index.html','r') as post:
			postscript=post.read() 

	chaine = preambule + lignes3 + lignes4 + en_tete + txt_lignes + postscript
	with open("/var/www/html/index.html",'w') as index_html:
			index_html.write(chaine)



def package_rec(instants_cumuls_i, S0_i, S1_i, cumul_NBB_out_i):
	os.nice(COURTOISIE) # la mise en boite des donnée est courtoise est courtoise
	# archivage d'images
	maintenant = datetime.datetime.now()
	date2 = maintenant.strftime('%Y_%m_%d_')
	heure2 = maintenant.strftime('%Hh%Mm%Ss')
	nom_fichier_brutes = hostname + "_acquisitions_brutes_" + date2 + heure2 +".csv" 
	chemin_dest_brutes = "/var/www/html/images_bugcount/"+nom_fichier_brutes
	
	with open(chemin_dest_brutes,'w') as mon_fichier:
		header = "t(microsec), S0, S1, NBB_out,\n" 
		mon_fichier.write(header)
		for i in range(1, len(instants_cumuls_i)):
			chaine = str(instants_cumuls_i[i]) + "," + str(S0_i[i]) + "," + \
				str(S1_i[i]) + "," +  str(cumul_NBB_out_i[i])  + '\n'
			mon_fichier.write(chaine)
	# ~ chemin_image_brutes ="/var/www/html/images_bugcount/images_brutes/"
	# ~ shutil.make_archive(chemin_dest_brutes, 'zip', chemin_image_brutes)
	# ~ nom_fichier_traitees = hostname + "_images_traitees" + date2 + heure2 
	# ~ chemin_dest_traitees = "/var/www/html/images_bugcount/"+nom_fichier_traitees
	# ~ chemin_image_traitees ="/var/www/html/images_bugcount/images_traitees/"
	# ~ shutil.make_archive(chemin_dest_traitees, 'zip', chemin_image_traitees)						

def package_images(fourmi):
	os.nice(COURTOISIE) # la mise en boite des donnée est courtoise est courtoise
	# archivage d'images
	maintenant = datetime.datetime.now()
	date2 = maintenant.strftime('%Y_%m_%d_')
	heure2 = maintenant.strftime('%Hh%Mm%Ss')
	nom_fichier_brutes = hostname + "_images_brutes_" + date2 + heure2 
	chemin_dest_brutes = "/var/www/html/images_bugcount/"+nom_fichier_brutes
	chemin_image_brutes ="/var/www/html/images_bugcount/images_brutes/"
	shutil.make_archive(chemin_dest_brutes, 'zip', chemin_image_brutes)
	nom_fichier_traitees = hostname + "_images_traitees" + date2 + heure2 
	chemin_dest_traitees = "/var/www/html/images_bugcount/"+nom_fichier_traitees
	chemin_image_traitees ="/var/www/html/images_bugcount/images_traitees/"
	shutil.make_archive(chemin_dest_traitees, 'zip', chemin_image_traitees)
	
	ref1 = "images_bugcount/" + nom_fichier_brutes + ".zip"
	ref2 = "images_bugcount/" + nom_fichier_traitees + ".zip"
	
	# lecture de la liste des images précédentes
	with open("/var/www/html/images.html", 'r') as mon_fichier:
		images_lignes = mon_fichier.read().splitlines()
		
	if fourmi: # affichage d'un message d'alerte en cas de présence d'une fourmi
		ligne = "<tr>" + "<td> <font color=#FF3333> ALERTE FOURMI : voir images ci-dessous </font> </td>" + "</tr>"
		images_lignes.append(ligne)
	ligne = "<tr>" + \
		"<td> <a href=" + ref1 + ">" + nom_fichier_brutes + ".zip" + "</a></td>" + \
		"<td> &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp; </td>" + \
		"<td> <a href=" + ref2 + ">" + nom_fichier_traitees + ".zip" + "</a></td>" +\
		"</tr>"
	images_lignes.append(ligne)
	
	# intercalaire si 3 lignes
	if len(images_lignes) % 4 == 0 :
		images_lignes.append("<tr> </tr> <tr> <td> <hr> </td> <td> <hr>  </td> <td> <hr> </td></tr> <tr>  </tr>\n")
	
	# sauvegarde des lignes 
	images_lignes_txt = " \n".join(images_lignes)
	with open("/var/www/html/images.html",'w') as mon_fichier:
			mon_fichier.write(images_lignes_txt)
	
	# lecture des header et footer
	with open('/var/www/html/pre_index_images.html','r') as preamb:
		preambule=preamb.read()       
	with open('/var/www/html/post_index_images.html','r') as post:
		postscript=post.read()
	# Affichage de la taille du dossier images
	stream=os.popen('du -sh /var/www/html/images_bugcount | cut -f 1')
	taille_images=stream.read()
	taille_image_ligne="<p> Taille du dossier images sur la carte SD : {} </p>".format(taille_images.strip())
	# mise à jour de l'interface html
	contenu = preambule + taille_image_ligne + images_lignes_txt + postscript #ajtp
	
	with open("/var/www/html/index_images.html",'w') as index_html:
			index_html.write(contenu)
	# effacement des images ayant servi à construire l'archive
	shutil.rmtree("/var/www/html/images_bugcount/images_brutes")
	shutil.rmtree("/var/www/html/images_bugcount/images_traitees")
	os.mkdir("/var/www/html/images_bugcount/images_brutes")
	os.mkdir("/var/www/html/images_bugcount/images_traitees")
	
def maj_graphique(instants_cumuls, cumul_NBB_out,nom_image):
	os.nice(COURTOISIE) # la maj graphique est courtoise
	fig=plt.figure()
	ax=fig.add_subplot(1,1,1)
	abscisses=[t.strftime("%H:%M:%S\n%d/%m/%Y") for t in instants_cumuls]
	plt.plot(abscisses,cumul_NBB_out, label = "NBB_out")
	# ~ plt.plot(abscisses,cumul_dg_nym, label = "dg_nym")
	# ~ plt.plot(abscisses,cumul_dg_adu, label = "dg_adu")
	plt.legend()
	ax.xaxis.set_major_locator(MaxNLocator(nbins=4))
	chemin_img = "/var/www/html/images_bugcount/"+nom_image
	plt.savefig(chemin_img)
	plt.close()
	
def maj_capteurs(S0, S1):
	os.nice(COURTOISIE) # la maj capteur est courtoise
	if (S0 == 1):
		shutil.copyfile("/var/www/html/images/ON.png", "/var/www/html/images_bugcount/live/image_S0.png")
	else:
		shutil.copyfile("/var/www/html/images/OFF.png", "/var/www/html/images_bugcount/live/image_S0.png")
	if (S1 == 1):
		shutil.copyfile("/var/www/html/images/ON.png", "/var/www/html/images_bugcount/live/image_S1.png")
	else:
		shutil.copyfile("/var/www/html/images/OFF.png", "/var/www/html/images_bugcount/live/image_S1.png")		
		
def maj_graphique3(instants_acquisition,taux_franchissement_montee,taux_franchissement_descente):
	os.nice(COURTOISIE) # la maj graphique est courtoise
	fig=plt.figure()
	ax=fig.add_subplot(1,1,1)
	abscisses=[t.strftime("%H:%M:%S\n%d/%m/%Y") for t in instants_acquisition]
	plt.plot(abscisses, taux_franchissement_montee, label = "montée")
	plt.plot(abscisses, taux_franchissement_descente, label = "descente")
	plt.legend()
	ax.xaxis.set_major_locator(MaxNLocator(nbins=4))
	plt.savefig("/var/www/html/images_bugcount/graphique3.png")
	plt.close()
