<!DOCTYPE html>
<html lang="en">
<head>
	<title>MiteThru</title>
	<meta charset="UTF-8">
	<meta name="viewport" content="width=device-width, initial-scale=1">
<!--===============================================================================================-->	
	<link rel="icon" type="image/png" href="images/icons/mite.ico"/>
<!--===============================================================================================-->
	<link rel="stylesheet" type="text/css" href="vendor/bootstrap/css/bootstrap.min.css">
<!--===============================================================================================-->
	<link rel="stylesheet" type="text/css" href="fonts/font-awesome-4.7.0/css/font-awesome.min.css">
<!--===============================================================================================-->
	<link rel="stylesheet" type="text/css" href="vendor/animate/animate.css">
<!--===============================================================================================-->
	<link rel="stylesheet" type="text/css" href="vendor/select2/select2.min.css">
<!--===============================================================================================-->
	<link rel="stylesheet" type="text/css" href="vendor/perfect-scrollbar/perfect-scrollbar.css">
<!--===============================================================================================-->
	<link rel="stylesheet" type="text/css" href="css/util.css">
	<link rel="stylesheet" type="text/css" href="css/main.css">
	<link rel="stylesheet" type="text/css" href="css/menus.css">
<!--===============================================================================================-->

</head>



<body>
	<div id="bloc_page">
		<!--#include file="header.html" -->


<h2>Configuration du miteThru</h2>

<?php
$freq = 5;
$mode = "normal";
$seuil_video = 3;
$duree_video = "10";
$interval_video = "230";

$file = "miteThru.conf";
$content = file_get_contents($file);
$tableau = explode("\n",$content);

$freq = explode("=",$tableau[0])[1];
$mode = explode("=",$tableau[1])[1];
$seuil_video = explode("=",$tableau[2])[1];
$duree_video = explode("=",$tableau[3])[1];
$interval_video = explode("=",$tableau[4])[1];
?>


<form action="/action_page.php" method="get">
  <label for="frequence">fréquence d'échantillonnage maximale (de 0 à 5 images par seconde; 0 correspond à la fréquence maximale):</label><br>
  <input type="text" id="freq" name="freq" value='<?php echo $freq; ?>'><br>
  
  <input type="radio" id="normal" name="mode" value="normal" <?php echo ($mode== 'normal') ?  "checked" : "" ;  ?> style="display:inline;" >
  <label for="normal" style="display:inline;">Normal</label><br><br>
  
  <input type="radio" id="video" name="mode" value="video"  <?php echo ($mode== 'video') ?  "checked" : "" ;  ?> style="display:inline;" >
  <label for="normal">Video</label><br><br>
  
  <input type="radio" id="calib" name="mode" value="calib"  <?php echo ($mode== 'calib') ?  "checked" : "" ;  ?> style="display:inline;" >
  <label for="video">Calibration</label><br><br>
  
    <input type="radio" id="calib_en_ligne" name="mode" value="calib_en_ligne"  <?php echo ($mode== 'calib_en_ligne') ?  "checked" : "" ;  ?> style="display:inline;" >
  <label for="calib_en_ligne">Calibration en ligne</label><br><br>
  
  <p>Si le mode "vidéo" ou "calibration en ligne" est sélectionné, les trois paramètres suivants sont à prendre en compte :</p>
  <label for="seuil_video">Nombre d'acariens simultanément suivis déclenchant l'acquisition d'une vidéo:</label><br>
  <input type="text" id="seuil_video" name="seuil_video" value='<?php echo $seuil_video; ?>'><br>
  <label for="duree_video">Durée d'une video en secondes:</label><br>
  <input type="text" id="duree_video" name="duree_video" value='<?php echo $duree_video; ?>'><br>
  <label for="interval_video">Intervalle entre 2 videos, en secondes:</label><br>
  <input type="text" id="interval_video" name="interval_video"  value='<?php echo $interval_video; ?>'><br>
  <input type="submit" value="Submit">
</form> 

<form action="/action_page.php" method="get">

</form> 


</body>
<footer height="200">
<p align="center"> L.Roy <a href="mailto:Lise.ROY@cefe.cnrs.fr">Lise.ROY@cefe.cnrs.fr </a> - CEFE - CNRS - 34090 Montpellier</p>
</html>

