#!/usr/bin/env python3

# 2023-05-21 - 0.0.1 - First release

import tools

import re

from argparse import ArgumentParser


def get_options():
    parser = ArgumentParser()
    parser.add_argument("-d", "--date", type=str, default="", help="Imported date", required=True)
    parser.add_argument("-f", "--file", type=str, default="", help="tetra file channel informations", required=True)
    parser.add_argument("-t", "--tdafile", type=str, default="", help="TETRAPOL Dump Analyzer", required=True)

    options = parser.parse_args()

    return options


def openFileInformations(options):
    fileinfos = {}
    with open(options.file) as f:
        lines = f.readlines()

        for line in lines:
            match = re.match("Relais +CCH +TCH",line.strip())
            if match:
                continue

            line = re.sub(" +", " ", line.strip())
            if line:
                lineinfos = line.split(" ")
                fileinfos[lineinfos[0]] = {
                "CCH": lineinfos[1],
                "TCH": lineinfos[2:]
                }
        
        return fileinfos

def sortByTowerid(line):
    match = re.match('^([0-9]+)\-([0-9]+)\-([0-9]+)',line.strip())
    if match:
        return f'{match[1].zfill(6)}{match[2].zfill(6)}{match[3].zfill(6)}'
    
    return ""

def writeFileInformations(options, entries):
    wtowerid=12
    columnspace=10
    dataspace=4

    title = f"{'Relais'.rjust(wtowerid)}{' '*columnspace}CCH {' '*columnspace}TCH "

    lines = []
    for towerid in entries:
        cch = str(entries[towerid]['CCH'])
        line = f"{towerid.rjust(wtowerid)}{' '*columnspace}{cch}{' '*columnspace}"

        entries[towerid]['TCH'].sort()
        for tch in entries[towerid]['TCH']:
            line += f"{tch}{' '*dataspace}"
        lines.append(line)

    lines.sort(key=sortByTowerid)

    with open(options.file,"w") as f:
        f.write(f"{title}\n")
        for line in lines:
            f.write(f"{line}\n")


def updateOnlyNew(options, channels):
    with open(options.tdafile) as f:
        lines = f.readlines()
        
        currentcellid = ""
        for line in lines:
            # Extract cellId
            match = re.match('Cellule ([0-9]+\-[0-9]+\-[0-9]+) du',line.strip())
            if match:
                currentcellid = match[1]

            # Extract CCH
            match = re.match('- Cellule ([0-9]+\-[0-9]+\-[0-9]+)\tCCH ([0-9]+)',line.strip())
            if match and currentcellid:
                newcellid = match[1]
                cch = match[2]
                channels.updateOrInsert(newcellid,"CCH",cch)

            # Search new TCH
            match = re.match('TCH : ([0-9]+.*)',line.strip())
            if match and currentcellid:
                channels.updateOrInsert(currentcellid,"TCH", match[1])


if __name__ == '__main__':
    options = get_options()

    channels = tools.Channels()
    channels.importFromFile(options.file)
    updateOnlyNew(options, channels)

    channels.exportToFile(options.file)
    channels.exportHistories(options.date, options.file)