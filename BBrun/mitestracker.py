# import the necessary packages
from centroidtracker import CentroidTracker
from collections import OrderedDict
from scipy.spatial import distance as dist
import math
# version miteThruv12 du 12/07/2020
class MitesTracker(CentroidTracker):
	""" classe permettant de tracker (dans un disque évidé de tracking) et de compter les acariens dans un disque évidé de comptage, situé à l'intérieur de la zone de tracking.
	version du 12 juillet 2020
"""
	def __init__(self, dim_img, border = ((300, 200), 200), trackingW = 150, countingW = 50, maxDisappeared=50):
		# initialisation du tracker
		CentroidTracker.__init__(self)
		self.number_astigmata_IN = 0 # le compteur du nombre d’acariens astigmates supposés ayant franchi la frontière pour monter sur le perchoir.
		self.number_astigmata_OUT = 0 # le compteur du nombre d’acariens astigmates supposés ayant franchi la frontière pour descendre du perchoir.
		self.number_dg_nymph_IN = 0 # le compteur du nombre d’acariens dermanyssus gallinae nymphes ayant franchi la frontière pour monter sur le perchoir.
		self.number_dg_nymph_OUT = 0 # le compteur du nombre d’acariens dermanyssus gallinae nymphes ayant franchi la frontière pour descendre du perchoir.
		self.number_dg_adult_IN = 0 # le compteur du nombre d’acariens dermanyssus gallinae adultes ayant franchi la frontière pour monter sur le perchoir.
		self.number_dg_adult_OUT = 0 # le compteur du nombre d’acariens dermanyssus gallinae adultes ayant franchi la frontière pour descendre du perchoir.
		self.nature = OrderedDict() # la nature des objets : ASTIGMATA , DG_NYMPH , DG_ADULT
		self.franchissement = OrderedDict() # le franchissement des objets : True si l'acarien est en train de franchir la frontière. False sinon
		self.couleur_ASTIGMATA = (0,255,255)
		self.couleur_DG_NYMPH = (255,0,0) #(128,128,255)
		self.couleur_DG_ADULT = (0,0,255)
		self.etat = OrderedDict() # l'etat des objets : IN or OUT
		(w, h) = dim_img
		aire_image = w * h
		aire_image_base = 704 * 528
		rapport = aire_image / aire_image_base
		self.AREA_MAX_ACA = 1500 *rapport  # du 24 janvier au 4 mars : 800
		self.AREA_ADULT_NYMPH = 200 * rapport # du 24 janvier au 4 mars : 90
		self.AREA_NYMPH_ASTIGM = 70 * rapport # du 24 janvier au 4 mars : 25
		self.AREA_MIN_ACA = 10 * rapport  # du 24 janvier au 4 mars : 10
		try:
			self.trackingW= trackingW # la largeur (en pixels) de la bande de tracking
			assert (trackingW > 50)
		except TypeError:
			print("Erreur dans la saisie de la saisie de la largeur de la zone de suivi.")
			raise
		except AssertionError:
			print("Il faut assurer la condition trackingW > 50.")
			raise 
		try:
			self.countingW= countingW # la largeur  (en pixels) de la bande de comptage
			assert (countingW > 0 and countingW < trackingW - 50)
		except TypeError:
			print("Erreur dans la saisie de la saisie de la largeur de la zone de comptage")
			raise
		except AssertionError:
			print("Il faut assurer les conditions countingW > 0 et countingW < trackingW - 50") 
			raise
		self.border = border 	# le cercle de la frontère sous la forme ((Cx, Cy), r), où Cx et Cy sont les 
					# coordonnées du cercle et r son rayon (en pixels) 
		try:
			((Cx, Cy), r) = self.border
			assert r > trackingW/2
		except TypeError:
			print("Erreur dans la saisie de la frontière, celle-ci doit être de la forme ((Cx, Cy), r)")
			raise
		except AssertionError:
			print("Il faut assurer la condition r > TrackingW/2") 
			raise

	def __repr__(self):
		return "Tracker défini par une : \n \t" + \
			"_frontière dont le centre est {} et le rayon vaut  {} pixels,  \n\t".format(self.border[0], self.border[1]) + \
			"_largeur de la zone de suivi : {}\n\t".format(self.trackingW) + \
			"_largeur de la zone de comptage : {}\n\t".format(self.countingW) + \
			"_nombre de trames avant perte du suivi : {}".format(self.maxDisappeared)
	
	def __sub__(self, mt_old):
		""" permet de calculer la variation totale d'entrée d'acariens entre 2 acquisitions
	"""
		montee = self.number_astigmata_IN - mt_old.number_astigmata_IN + self.number_dg_nymph_IN - mt_old.number_dg_nymph_IN + self.number_dg_adult_IN - mt_old.number_dg_adult_IN
		#print("montee = {} - {} + {} - {} + {} - {}".format(self.number_astigmata_IN , mt_old.number_astigmata_IN , self.number_dg_nymph_IN , mt_old.number_dg_nymph_IN , self.number_dg_adult_IN , mt_old.number_dg_adult_IN))
		descente = self.number_astigmata_OUT - mt_old.number_astigmata_OUT + self.number_dg_nymph_OUT - mt_old.number_dg_nymph_OUT + self.number_dg_adult_OUT - mt_old.number_dg_adult_OUT
		return (montee, descente)
	
	def register(self, mite_coord, rayon):
		d = dist.euclidean(mite_coord, self.border[0]) # calcul de la distance entre le nouveau acarien et le centre de la frontière
		r = self.border[1] # le rayon de la frontière
		self.areas[self.nextObjectID] = math.pi * rayon ** 2
		if (self.areas[self.nextObjectID] < self.AREA_NYMPH_ASTIGM) :
			self.nature[self.nextObjectID] = 'ASTIGMATA'
		elif (self.areas[self.nextObjectID] < self.AREA_ADULT_NYMPH ) :
			self.nature[self.nextObjectID] = 'DG_NYMPH'
		else:
			self.nature[self.nextObjectID] = 'DG_ADULT'
		if (d >= r) :  
			self.etat[self.nextObjectID]='OUT' #l'accarien apparait à l'extérieur dans la zone de tracking
		if (d < r) :
			self.etat[self.nextObjectID]='IN' #l'accarien apparait à l'intérieur dans la zone de tracking
		CentroidTracker.register(self, mite_coord, rayon) # à mettre à la fin car incrémentation de nextObjectID
		if self.nextObjectID == 100000:
			self.nextObjectID = 0

	def deregister(self, objectID):
		# to deregister an object ID we delete the object ID from
		# both of our respective dictionaries
		#print("effacement de l'objet {} : {}".format(objectID, self.franchissement[objectID])) #ajtp
		del self.etat[objectID]
		del self.nature[objectID]
		del self.franchissement[objectID]
		CentroidTracker.deregister(self, objectID)
		
		
	def update(self, cercls):
		CentroidTracker.update(self, cercls)
		# mise à jour de l'état ('IN' ou 'OUT')
		for objectID in self.objects.keys(): 
			self.franchissement[objectID]=False # par défaut, l'accarien ne franchit pas la frontière
			d = dist.euclidean(self.objects[objectID], self.border[0]) # calcul de la distance entre l'acarien et le centre de la frontière
			r = self.border[1] # le rayon de la frontière
			if (self.etat[objectID]=='OUT') and (d < (r - self.countingW/2)):  
				self.franchissement[objectID]=True #l'accarien franchit la frontière
				self.etat[objectID]='IN' #l'accarien est à l'intérieur de la frontière
				if (self.areas[objectID] < self.AREA_NYMPH_ASTIGM) :
					self.nature[objectID] = 'ASTIGMATA'
					self.number_astigmata_IN += 1
				elif (self.areas[objectID] < self.AREA_ADULT_NYMPH ) :
					self.nature[objectID] = 'DG_NYMPH'
					self.number_dg_nymph_IN += 1
				else:
					self.nature[objectID] = 'DG_ADULT'
					self.number_dg_adult_IN += 1
				#print("franchissement de l'objet {} : {}".format(objectID, self.franchissement[objectID])) #ajtp
			if (self.etat[objectID]=='IN')  and (d > (r + self.countingW/2)): 
				self.franchissement[objectID]=True #l'accarien franchit la frontière
				self.etat[objectID]='OUT' #l'accarien est à l'extérieur de la frontière
				if (self.areas[objectID] < self.AREA_NYMPH_ASTIGM) :
					self.nature[objectID] = 'ASTIGMATA'
					self.number_astigmata_OUT += 1
				elif (self.areas[objectID] < self.AREA_ADULT_NYMPH ) :
					self.nature[objectID] = 'DG_NYMPH'
					self.number_dg_nymph_OUT += 1
				else:
					self.nature[objectID] = 'DG_ADULT'
					self.number_dg_adult_OUT += 1
				#print("franchissement de l'objet {} : {}".format(objectID, self.franchissement[objectID])) #ajtp
			if ((d > (r + self.trackingW/4)) or (d < (r - self.trackingW/4))):
				# pour effacement des objets sortis de la zone de tracking
				self.disappeared[objectID] += self.maxDisappeared +1 
			
		
		# effacement des objets sortis de la zone de tracking
		disappeared2 = self.disappeared.copy()
		for objectID in disappeared2.keys():
			if disappeared2[objectID] > self.maxDisappeared:
				self.deregister(objectID)
		
				
		return self.objects

