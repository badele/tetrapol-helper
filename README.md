# tetrapol-helper

Helper for using with tetrapol-kit

## Usage

### Demodolation & Decoding

```console
python tetrapol-helper.py --file tetrapol_french_channels.txt -m "-a rtl=0 -p 7 -g 42 -s 2000000" --cellid "340-0-6" --username badele
```

### Extraction tda_analyse_cellule
```console
python tetrapol-extract-onlynew.py -f tetrapol_french_channels.txt -t extraction_td_analyze.txt -d "2023-05-21"
```

### Hz <> Channel conversion

```console
python tetrapol-converter.py -f 392.175M
392.175 MHz => 2353
```

```console
python tetrapol-converter.py -c 2353
2353 => 392.175 MHz 
```

### Sample output helper commands

```console
python tetrapol-helper.py --file tetrapol_french_channels.txt -m "-a rtl=0 -p 7 -g 42 -s 2000000" --cellid "340-0-6" --username badele
```

```console
# Generated by tetrapol-helper
# Get tetrapol informations for 340-0-6 tower

# == Requirements installation ==
# All installations will be done on the /tmp/tetrapol-helper (mkdir /tmp/tetrapol-helper)
# Thank syracuse for demod_syracuse.py project
# Thank mrousse83 for the TETRAPOL Dump Analyzer project
mkdir -p /tmp/tetrapol-helper
# Download manually "pack_tplm_v831.zip" from this URL https://forum.tetrahub.net/download/file.php?id=737
wget https://www.cjoint.com/doc/23_04/MDxqjcBJdcH_tda-analyse-cellule.zip
unzip /tmp/tetrapol-helper/*.zip

# Fifo creation (for demoluation)
rm -f /tmp/tetrapol-helper/channel2352.bits && mkfifo /tmp/tetrapol-helper/channel2352.bits
rm -f /tmp/tetrapol-helper/channel2328.bits && mkfifo /tmp/tetrapol-helper/channel2328.bits
rm -f /tmp/tetrapol-helper/channel2288.bits && mkfifo /tmp/tetrapol-helper/channel2288.bits

# == Demodulation ==
python3 demod_syracuse.py -a rtl=0 -p 7 -g 42 -s 2000000 -c 2352,2328,2288

# == Decoding / Dump ==
# On terminal 1
tetrapol_dump -d DOWN -t CCH -i /tmp/tetrapol-helper/channel2352.bits 2>&1 >/dev/null | python3 tda_analyse_cellule.py

# On terminal 2
tetrapol_dump -d DOWN -t TCH -i /tmp/tetrapol-helper/channel2328.bits 2>&1 >/dev/null | python3 tda_analyse_cellule.py

# On terminal 2
tetrapol_dump -d DOWN -t TCH -i /tmp/tetrapol-helper/channel2288.bits 2>&1 >/dev/null | python3 tda_analyse_cellule.py
```

##