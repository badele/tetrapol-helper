#!/usr/bin/env python3

# 2023-05-20 - 0.0.1 - First release
# 2023-05-21 - 0.0.2 - Add write output to file / Rename tower command line option to cellid
# 2023-05-21 - 0.0.3 - Fix not existant cellId

import tools

import re
import sys
import argparse 


def get_options():
    parser = argparse.ArgumentParser()
    parser.add_argument("-f", "--file", type=str, default="", help="tetra file channel informations", required=True)
    parser.add_argument("-c", "--cellid", type=str, default="", help="Cell Id", required=True)
    parser.add_argument("-m", "--demodulation", type=str, default="", help="Demodulation options", required=True)
    parser.add_argument("-s", "--saveto", type=str, default="/tmp/tetrapol-helper", help="Save result to", required=False)
    parser.add_argument("-e", "--exclude", type=str, default="", help="Exclude channels", required=False)
    parser.add_argument("-w","--write", action=argparse.BooleanOptionalAction)

    options = parser.parse_args()

    return options


def getFileInformations(options):
    fileinfos = {}
    with open(options.file) as f:
        lines = f.readlines()

        for line in lines:
            line = re.sub(" +", " ", line.strip())
            if line:
                lineinfos = line.split(" ")
                fileinfos[lineinfos[0]] = {
                "CCH": lineinfos[1],
                "TCH": lineinfos[2:]
                }
        
        return fileinfos

def getCellInformations(options):
    with open(options.file) as f:
        lines = f.readlines()

        for line in lines:
            line = re.sub(" +", " ", line.strip())
            if line:
              infos = line.split(" ")
              if infos[0] == options.cellid:
                return infos

        return None


def getSteps(options, cellinfo):
    channels = cellinfo["TCH"]

    includes = [cellinfo['CCH']]
    includes = includes + cellinfo["TCH"]

    excludes = []
    if options.exclude:
        for exclude in options.exclude.split(','):
            includes.remove(int(exclude))
            excludes.append(int(exclude))

    steps = f"""# Generated by tetrapol-helper
# Get tetrapol informations for {options.cellid} cellId
# {" ".join(sys.argv).replace(options.demodulation,f"'{options.demodulation}'")}

# == Requirements installation ==
# All installations will be done on the {options.saveto} (mkdir {options.saveto})
# Thank syracuse for demod_syracuse.py project 
# Thank mrousse83 for the TETRAPOL Dump Analyzer project 
mkdir -p {options.saveto} && cd {options.saveto} 
# Download manually "pack_tplm_v831.zip" from this URL https://forum.tetrahub.net/download/file.php?id=737
wget https://www.cjoint.com/doc/23_04/MDxqjcBJdcH_tda-analyse-cellule.zip
unzip {options.saveto}/*.zip

# Fifo creation (for demodulation)
rm -f {options.saveto}/channel{cellinfo['CCH']}.bits && mkfifo {options.saveto}/channel{cellinfo['CCH']}.bits
"""

    for tch in cellinfo['TCH']:
        if tch not in includes:
            continue
        
        steps += f"rm -f {options.saveto}/channel{tch}.bits && mkfifo {options.saveto}/channel{tch}.bits\n"

    strincludes = list(map(str, includes))
    steps += f"""
# == Demodulation ==
python3 demod_syracuse.py {options.demodulation} -c {",".join(strincludes)}

# == Decoding / Dump ==
# On terminal 1
"""

    if options.write:
        steps += f"tetrapol_dump -d DOWN -t CCH -i {options.saveto}/channel{cellinfo['CCH']}.bits 1>{options.saveto}/channel{cellinfo['CCH']}.stdout 2>{options.saveto}/channel{cellinfo['CCH']}.stderr" 
    else:
        steps += f"tetrapol_dump -d DOWN -t CCH -i {options.saveto}/channel{cellinfo['CCH']}.bits 2>&1 >/dev/null | python3 tda_analyse_cellule.py {cellinfo['CCH']}" 

    tid = 2
    for tch in cellinfo['TCH']:
        if tch not in includes:
            continue

        steps += f"""
# On terminal {tid}
"""

        if options.write:
            steps += f"tetrapol_dump -d DOWN -t TCH -i {options.saveto}/channel{tch}.bits 1>{options.saveto}/channel{tch}.stdout 2>{options.saveto}/channel{tch}.stderr"
        else:
            steps += f"tetrapol_dump -d DOWN -t TCH -i {options.saveto}/channel{tch}.bits 2>&1 >/dev/null | python3 tda_analyse_cellule.py {tch}"
        tid += 1

    print(steps)

if __name__ == '__main__':
    options = get_options()

    channels = tools.Channels()
    channels.importFromFile(options.file)

    tinfos = channels.getCellInfos(options.cellid)

    # tinfos = getCellInformations(options)
    if tinfos:
        getSteps(options, tinfos)
    else:
        print(f"No {options.cellid} cellId found")
        sys.exit(1)