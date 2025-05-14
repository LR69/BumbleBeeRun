import numpy as np
import cv2
#from skimage.feature import peak_local_max
#from skimage.morphology import watershed
#from scipy import ndimage
import time
import math

# version miteThruv9b du 19/01/20
# version du 24/01/20 : ajout détection fourmi

substractor = cv2.createBackgroundSubtractorMOG2(history = 100, varThreshold=25, detectShadows=True)

def bugcount(img,masque, aire_min, aire_max, mode = "hide"):
	fourmi = False
	if mode == "show":
		cv2.imshow('image brute',img) # ajtp
		cv2.imshow('masque brute',masque) # ajtp
		#key = cv2.waitKey(0)
	# filtrage
	gray = cv2.cvtColor(img,cv2.COLOR_BGR2GRAY)
	# effacement de l'arrière plan 
	bkgd_sup = substractor.apply(gray)
	if mode == "show":
		cv2.imshow('suppression arrière plan',bkgd_sup) # ajtp
		#key = cv2.waitKey(0)
	# masquage "doonut"
	masque2 = cv2.bitwise_and(bkgd_sup , masque , mask=None)
	if mode == "show":
		cv2.imshow('masque',masque2) # ajtp
		#key = cv2.waitKey(0)
		
	# détermination des contours
	_, contours, _ = cv2.findContours(masque2.copy(),cv2.RETR_EXTERNAL,cv2.CHAIN_APPROX_SIMPLE)
	cercles=[]
	for c in contours:
		M = cv2.moments(c)
		aire = (M['m00'])
		if ((aire > aire_min) and (aire <= aire_max )): 
			centre = ((M['m10']/M['m00']), (M['m01']/M['m00']))
			rayon = math.sqrt(aire/math.pi)
			cercle = (centre, rayon)
			cercles.append(cercle)
		if (aire > aire_max):
			fourmi =  True
	if mode == "debug":
		print("[INFO] {} unique segments found".format(len(cercles))) 

	return (cercles, fourmi)

