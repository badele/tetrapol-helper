#!/usr/bin/env python3

import sys

import os
import re
import datetime

def sortByTowerid(line):
    match = re.match('^([0-9]+)\-([0-9]+)\-([0-9]+)',line.strip())
    if match:
        return f'{match[1].zfill(6)}{match[2].zfill(6)}{match[3].zfill(6)}'
    
    return ""


class Channels:
    def __init__(self):
        self.__channels = {}
        self.__new = {}
        self.__update = {}
        self.__wtowerid=10


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


    def getCellInfos(self, towerid):
        return self.__channels[towerid]


    def exportHistories(self, date, filename):
        hfilename = os.path.splitext(filename)[0]

        with open(f"{hfilename}.histo","a") as f:
            # Show New
            for cellid in self.__new:
                cch = self.__new[cellid]['CCH']
                tch = self.__new[cellid]['TCH']

                output = f"{date} -    New Cell {cellid.rjust(self.__wtowerid)}"
                if cch:
                    output +=f" CCH: {cch}" 

                if tch:
                    output +=f" TCH: {tch}" 
                
                f.write(f"{output}\n")

            # Show New
            for cellid in self.__update:
                output = f"{date} - Update Cell {cellid.rjust(self.__wtowerid)}"
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

        title = f"{'Relais'.rjust(self.__wtowerid)}{' '*columnspace}CCH {' '*columnspace}TCH "

        lines = []
        for towerid in self.__channels:
            cch = str(self.__channels[towerid]['CCH'])
            # if cch == "":
            #     cch = " "*4
            line = f"{towerid.rjust(self.__wtowerid)}{' '*columnspace}{cch}{' '*columnspace}"

            self.__channels[towerid]['TCH'].sort()
            for tch in self.__channels[towerid]['TCH']:
                line += f"{tch}{' '*dataspace}"
            lines.append(line)

        lines.sort(key=sortByTowerid)

        with open(filename,"w") as f:
            f.write(f"{title}\n")
            for line in lines:
                f.write(f"{line}\n")
