# Source: from tetrahub site(mrousse83)

# TETRAPOL Dump - Analyse Cellule

APPLICATION_NOM = "TETRAPOL Dump Analyzer - Analyse Cellule"

import tools

import datetime
import re
import sys
import time

from argparse import ArgumentParser

d_system_info = False
d_neighbouring_cell = False
deja_affiche = False
departement = "???"
tda_conf = dict()
tda_tch = dict()
tda_tkg = dict()

class timedeltaplus24h(datetime.timedelta):
	def __str__(self):
		secondes = self.total_seconds()
		heures = secondes // 3600
		minutes = (secondes % 3600) // 60
		secondes = secondes % 60
		str = '{:02d}:{:02d}:{:02d}'.format(int(heures), int(minutes), int(secondes))
		return(str)

def get_options():
    parser = ArgumentParser()
    parser.add_argument("-u", "--username", type=str, default="", help="Username made scan", required=False)
    parser.add_argument('-v', '--version', action='version', version=f'{tools.__name__} {tools.__version__} - %(prog)s - {APPLICATION_NOM}')

    try:
        options = parser.parse_args()
    except:
        parser.print_help()
        sys.exit(0)

    return options


def analyse_bloc(bloc):
	global d_system_info
	global d_neighbouring_cell
	global deja_affiche
	global departement
	global log
	global tda_conf
	global tda_tch
	global tda_tkg
	
	# Récupération du numéro CODOP
	codop = re.search("CODOP=0x(\d+)", bloc)
	# S'il est présent
	if codop:
		# D_SYSTEM_INFO (0x90)
		if codop.group(1) == "90":
			if not d_system_info:
				# Pays
				country_code = re.search("COUNTRY_CODE=(\d+)", bloc)
				pays = "- Pays : "
				if int(country_code.group(1)) == 1:
					pays += "France [1]"
				else:
					pays += "Inconnu (" + country_code.group(1) + ")"
				
				# Département
				dep = re.search("BN_ID=(\d+)", bloc)
				
				# Cellule
				cell_id = re.search("CELL_ID=(\d{3}-\d{1}-\d{1,2})", bloc)
				departement = cell_id.group(1)[0:3]
				
				# Réseau
				network = re.search("NETWORK=(\d+)", bloc)
				reseau = "- Réseau : "
				if int(network.group(1)) == 1:
					reseau += "INPT [1]"
				elif int(network.group(1)) == 2:
					reseau += "RUBIS / CORAIL-NG [2]"
				else:
					reseau += "Inconnu (" + network.group(1) + ")"
				
				# Système
				version = re.search("VERSION=(\d+)", bloc)
				systeme = "- Système : "
				if int(version.group(1)) == 5:
					systeme += "Tetrapol-TDM X.25 [5]"
				elif int(version.group(1)) == 6:
					systeme += "Tetrapol-IP [6]"
				else:
					systeme += "Inconnu (" + version.group(1) + ")"
				
				# Validation de la détection
				d_system_info = True
				
				# Affichage des informations
				log_cellule = "Cellule %s du département %s :" % (cell_id.group(1), dep.group(1).zfill(2))
				print(log_cellule)
				print(pays)
				print(reseau)
				print(systeme)
				
				# Log des informations
				log.write(log_cellule + "\n")
				log.write(pays + "\n")
				log.write(reseau + "\n")
				log.write(systeme + "\n")
		
		# D_NEIGHBOURING_CELL (0x94)
		if codop.group(1) == "94":
			if d_system_info and not d_neighbouring_cell:
				# Récupération du nombre de cellules voisines
				ccr_config = re.search("CCR_CONFIG=(\d+)", bloc)
				# Récupération des différentes informations
				liste_ccr_param = re.findall("BN_NB=(\d+) CHANNEL_ID=(\d+) ADJACENT_PARAM=\d+ BN=\d+ LOC=\d+ EXP=\d+ RXLEV_ACCESS=\d+", bloc)
				liste_cell_id = re.findall("CELL_ID BS_ID=(\d+) RSW_ID=(\d+)", bloc)
				liste_cell_bn = re.findall("CELL_BN=(\d+)", bloc)
				
				# Affichage des informations
				print("Liste des cellules voisines :")
				log.write("Liste des cellules voisines :\n")
				for i in range(int(ccr_config.group(1))):
					if int(liste_ccr_param[i][0]) == 0:
						cellule = departement
					else:
						cellule = liste_cell_bn[int(liste_ccr_param[i][0])-1]
					log_cellules_voisines = "- Cellule %s-%s-%s\tCCH %s" % (cellule, liste_cell_id[i][1], liste_cell_id[i][0], liste_ccr_param[i][1])
					print(log_cellules_voisines)
					log.write(log_cellules_voisines + "\n")
				
				# Validation de la détection
				d_neighbouring_cell = True
		
		if d_system_info and d_neighbouring_cell:
			if not deja_affiche:
				print("Analyse du flux pour récupérer les TCH, CONF et TKG :")
				deja_affiche = True
		
		# D_GROUP_ACTIVATION (0x55)
		if codop.group(1) == "55":
			if d_system_info and d_neighbouring_cell:
				activation_mode = re.search("HOOK=(\d+) TYPE=(\d+)", bloc)
				group_id = re.search("GROUP_ID=(\d+)", bloc)
				coverage_id = re.search("COVERAGE_ID=(\d+)", bloc)
				channel_id = re.search("CHANNEL_ID=(\d+)", bloc)
				
				# TCH
				if not channel_id.group(1) in tda_tch.keys():
					horaire = time.strftime("%d/%m/%Y à %H:%M:%S", time.localtime(time.time()))
					tda_tch.update({channel_id.group(1) : horaire})
					print("%s - TCH %s" % (horaire, channel_id.group(1)))
					
				# CONF
				if activation_mode.group(2) == "0":
					if not coverage_id.group(1) in tda_conf.keys():
						horaire = time.strftime("%d/%m/%Y à %H:%M:%S", time.localtime(time.time()))
						tda_conf.update({coverage_id.group(1) : horaire})
						print("%s - CONF %s" % (horaire, coverage_id.group(1)))
					
				# TKG
				elif activation_mode.group(2) == "1":
					if not group_id.group(1) in tda_tkg.keys():
						horaire = time.strftime("%d/%m/%Y à %H:%M:%S", time.localtime(time.time()))
						tda_tkg.update({group_id.group(1) : horaire})
						print("%s - TKG %s" % (horaire, group_id.group(1)))

# Show help if no arguments
options = get_options()

# Ouverture du fichier de log
fichier_log = "TETRAPOL-TDA-" + time.strftime("%Y%m%d-%H%M%S", time.localtime(time.time())) + ".txt"
log = open(fichier_log, "a")

debut = time.time()
snow = time.strftime("%d/%m/%Y à %H:%M:%S", time.localtime(debut))
tmp_debut = f"Début de l'analyse le {snow}"
if options.username:
	tmp_debut += f" effectué par {options.username}" 
print(tmp_debut)
log.write(tmp_debut + "\n")

try:
	# Traitement du flux entrant
	lignes = ""
	traitement = False
	for ligne in sys.stdin:		
		# Traitement de la ligne
		if ligne.strip() == "tetrapol:72":
			lignes = ligne
			traitement = True
		elif ligne[0] == "\t" and traitement == True:
			lignes += ligne
		elif ligne[0] != "\t" and traitement == True:
			analyse_bloc(lignes)
			traitement = False
finally:
	fin = time.time()
	tmp_fin = "Fin de l'analyse le " + time.strftime("%d/%m/%Y à %H:%M:%S", time.localtime(fin))
	print(tmp_fin)
	duree = "Durée de l'analyse : " + str(timedeltaplus24h(seconds=fin-debut))
	print(duree)
	
	# Enregistrement TCH
	tda_tch = dict(sorted(tda_tch.items()))
	tmp = ""
	tmp	= ", ".join(tda_tch)
	if not tmp:
		tmp = "Aucun"
	log.write("TCH : " + tmp + "\n")

	# Enregistrement CONF
	tda_conf = dict(sorted(tda_conf.items()))
	tmp = ""
	tmp	= ", ".join(tda_conf)
	if not tmp:
		tmp = "Aucun"
	log.write("CONF : " + tmp + "\n")
	
	# Enregistrement TKG
	tda_tkg = dict(sorted(tda_tkg.items()))
	tmp = ""
	tmp	= ", ".join(tda_tkg)
	if not tmp:
		tmp = "Aucun"
	log.write("TKG : " + tmp + "\n")
	
	log.write(tmp_fin + "\n")
	log.write(duree + "\n")
	
	# Fermeture du fichier de log
	log.close()