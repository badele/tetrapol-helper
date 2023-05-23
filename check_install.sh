#/usr/bin/env bash

DST="/tmp/tetrapol-helper"
GREEN=$(tput setaf 2) 
YELLOW=$(tput setaf 3)
RED=$(tput setaf 1)
NC="$(tput sgr0)"

width=40

checkTools() {
    alltools=1
    for tool in $1; do

        if command -v "${tool}" > /dev/null; then
            status="[✔️]"
            color="${GREEN}"
        else
            if command -v "./${tool}" > /dev/null; then
                status="[.]"
                color="${YELLOW}"
            else
                alltools=0
                status="[!]"
                color="${RED}"
            fi
        fi

        printf "%-${width}s %s%s%s\n" "${tool}" "${color}" "${status}" "${NC}"
    done

    echo ""
    printf "${YELLOW}[.]${NC}=$PWD\n"

    if [ ${alltools} -eq 0 ]; then
        echo "⚠️ Please verify your installation"
        exit 1
    fi

}

echo "🔎 tetrapol-helper installaction checker 🔎"
echo
checkTools "tetrapol_dump tetrapol-helper.py demod_syracuse.py tda_analyse_cellule.py"
