#!/usr/bin/env python3

# 18/04/2023 - 0.1 - Traitement du D_SYSTEM_INFO
# 19/04/2023 - 0.2 - Traitement du D_NEIGHBOURING_CELL
# 19/04/2023 - 0.3 - Traitement du D_GROUP_ACTIVATION
# 20/04/2023 - 0.4 - Correction d'un bug d'affichage
# 20/04/2023 - 0.5 - Ajout du calcul de la durée de l'analyse
# 20/04/2023 - 0.6 - Correction d'un bug d'affichage avec les départements dont le numéro est sur un seul chiffre
# 23/04/2023 - 0.7 - Ajout d'un paramètre obligatoire : numéro de CCH
# 22/05/2023 - 0.8 - Ajout des options de la ligne de commande
# 22/05/2023 - 0.9 - Généralisation du versionning
# 22/05/2023 - 0.10 - Ajout du nom de l'utilisateur dans le module tetrapol-helper
# 22/05/2023 - 0.11 - Ajout de tetrapol-converter.py
# 23/05/2023 - 0.12 - Add demod_syracuse.py and check_insgtall script

import sys

import os
import re
import datetime

__name__="TETRAPOL Helper"
__version__="0.12"

freqUnit = {
'G': 1000000000,
'M': 1000000,
"K": 1000,
}

def sortByCellId(line):
    match = re.match('^([0-9]+)\-([0-9]+)\-([0-9]+)',line.strip())
    if match:
        return f'{match[1].zfill(6)}{match[2].zfill(6)}{match[3].zfill(6)}'
    
    return ""

def freqToHz(freqstr):
    match = re.match("([0-9]+\.?[0-9]+)([Gg|Mm|Kk]?)",freqstr)
    if match:
        if not match[2]:
            return float(freqstr)

        multiplier = freqUnit[match[2].upper()]
        return float(match[1])*multiplier


def freqToStr(freqhz):
    unit=""

    if freqhz>=1000000000:
        freqhz /= 1000000000
        unit ="G"
    elif freqhz>=1000000:
        freqhz /= 1000000
        unit ="M"
    elif freqhz>=1000:
        freqhz /= 1000
        unit ="K"

    unit += "Hz"
    return f"{freqhz} {unit}"


def convertFreqToChannel(freqhz):
     return int((freqhz - 368645000) / 10000)


def convertChannelToFreq(channel):
    return 10000*channel+368645000


class Channels:
    def __init__(self):
        self.__channels = {}
        self.__new = {}
        self.__update = {}
        self.__wcellid=10


    def insert(self, cellid, value):
        self.__channels[cellid] = value


    def updateOrInsert(self, cellid, field, value):
        new = False
        update = False

        # If not exists, it's new entry
        if cellid not in self.__channels: 
            new = True
            self.__channels[cellid] = {
                "CCH": "xxxx",
                "TCH": []
            }

        # CCH
        if field == "CCH":
            oldvalue = self.__channels[cellid][field] 

        # TCH
        if field == "TCH":
            oldvalue = self.__channels[cellid][field]
            oldvalue.sort()

            value = value.replace(" ","").split(",")
            value = list(map(int, value))
            value.sort()
 
        # Update field value
        if not new and value != oldvalue:
            update = True
            self.__update[cellid] = {
                field: {
                'old': oldvalue
                }
            } 

        if new:
            self.__new[cellid] = self.__channels[cellid]
        
        if update:
            self.__update[cellid][field]['new'] = value

        self.__channels[cellid][field] = value


    def getCellInfos(self, cellid):
        if cellid not in self.__channels:
            return ""

        return self.__channels[cellid]


    def exportHistories(self, date, filename):
        hfilename = os.path.splitext(filename)[0]

        with open(f"{hfilename}.histo","a") as f:
            # Show New
            for cellid in self.__new:
                cch = self.__new[cellid]['CCH']
                tch = self.__new[cellid]['TCH']

                output = f"{date} -    New Cell {cellid.rjust(self.__wcellid)}"
                if cch:
                    output +=f" CCH: {cch}" 

                if tch:
                    output +=f" TCH: {tch}" 
                
                f.write(f"{output}\n")

            # Show New
            for cellid in self.__update:
                output = f"{date} - Update Cell {cellid.rjust(self.__wcellid)}"
                if 'CCH' in self.__update[cellid]: 
                    output += f" CCH: {self.__update[cellid]['CCH']['old']} => {self.__update[cellid]['CCH']['new']}"
                if 'TCH' in self.__update[cellid]: 
                    output += f" TCH: {self.__update[cellid]['TCH']['old']} => {self.__update[cellid]['TCH']['new']}"
                # if 'TCH' in self.__update[cellid]: 
                #     print(self.__update[cellid]['TCH'])
                
                f.write(f"{output}\n")

    def importFromFile(self, filename):
        with open(filename) as f:
            lines = f.readlines()

            for line in lines:
                match = re.match("Relais +CCH +TCH",line.strip())
                if match:
                    continue

                line = re.sub(" +", " ", line.strip())
                if line:
                    # Cell infos
                    lineinfos = line.split(" ")
                    cellinfo = {
                        "CCH": "xxxx",
                        "TCH": []
                    }
                    if len(lineinfos)>=2:
                       cellinfo['CCH'] = lineinfos[1]
                    if len(lineinfos)>=3:
                        
                        lineinfos[2:].sort()
                        cellinfo['TCH'] = list(map(int, lineinfos[2:]))

                    self.insert(lineinfos[0],cellinfo)


    def exportToFile(self, filename):
        columnspace=10
        dataspace=4

        title = f"{'Relais'.rjust(self.__wcellid)}{' '*columnspace}CCH {' '*columnspace}TCH "

        lines = []
        for cellid in self.__channels:
            cch = str(self.__channels[cellid]['CCH'])
            # if cch == "":
            #     cch = " "*4
            line = f"{cellid.rjust(self.__wcellid)}{' '*columnspace}{cch}{' '*columnspace}"

            self.__channels[cellid]['TCH'].sort()
            for tch in self.__channels[cellid]['TCH']:
                line += f"{tch}{' '*dataspace}"
            lines.append(line)

        lines.sort(key=sortByCellId)

        with open(filename,"w") as f:
            f.write(f"{title}\n")
            for line in lines:
                f.write(f"{line}\n")
