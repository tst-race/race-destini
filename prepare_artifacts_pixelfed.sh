#!/usr/bin/env bash
# -----------------------------------------------------------------------------
# Script to prepare to the plugin/artifacts dir for publishing to Jfrog Artifactory
# -----------------------------------------------------------------------------

set -xe
CALL_NAME="$0"


###
# Helper functions
###


# Load Helper Functions
BASE_DIR=$(cd $(dirname ${BASH_SOURCE[0]}) >/dev/null 2>&1 && pwd)
. ${BASE_DIR}/helper_functions.sh


###
# Arguments
###

# Version values
RACE_VERSION="1.4.0"

HELP=\
'Script to prepare to the plugin/artifacts dir for publishing to Jfrog Artifactory
Examples: 
    ./prepare_artifacts.sh 
'

# Parse CLI Arguments
while [ $# -gt 0 ]
do
    key="$1"

    case $key in

        -h|--help)
        printf "%s" "${HELP}"
        exit 1;
        ;;

        --*)
        shift
        break
        ;;
        *)
        echo "${CALL_NAME} unknown argument \"$1\""
        exit 1
        ;;
    esac
done


###
# Main Execution
###


formatlog "INFO" "Cleaning plugin/artifacts Before Building Artifacts"
#bash ${BASE_DIR}/clean_artifacts.sh

rm -rf ${CURRENT_DIR}/pixelfed-plugin/artifacts/android-arm64-v8a-client/*
rm -rf ${CURRENT_DIR}/pixelfed-plugin/artifacts/linux-arm64-8va-client/*
rm -rf ${CURRENT_DIR}/pixelfed-plugin/artifacts/linux-arm64-8va-server/*
rm -rf ${CURRENT_DIR}/pixelfed-plugin/artifacts/android-x86_64-client/*
rm -rf ${CURRENT_DIR}/pixelfed-plugin/artifacts/linux-x86_64-client/*
rm -rf ${CURRENT_DIR}/pixelfed-plugin/artifacts/linux-x86_64-server/*



formatlog "INFO" "Moving Android arm64 Client Files (Nothing to Build)"
DEST_DIR="${BASE_DIR}/pixelfed-plugin/artifacts/android-arm64-v8a-client/DestiniPixelfed"
mkdir -p ${DEST_DIR}
cp -rf source/*.py ${DEST_DIR}
cp -rf source/pixelfed/*.py ${DEST_DIR}
mkdir -p ${DEST_DIR}/scripts
cp source/scripts/common/* ${DEST_DIR}/scripts 
# Renaming to jel2_Pixelfed_codec_android.sh
cp -f source/scripts/pixelfed/jel2_Pixelfed_codec_android_arm64.sh ${DEST_DIR}/scripts/jel2_Pixelfed_codec_android.sh
cp -rf source/pixelfed/manifest.pixelfed.json ${DEST_DIR}/manifest.json
cp -rf source/auth.json ${DEST_DIR}/auth.json
cp -rf source/bin ${DEST_DIR}
mkdir -p ${DEST_DIR}/libs
cp -rf source/libs/arm64/*.so ${DEST_DIR}/libs
rm -rf ${DEST_DIR}/covers
mkdir -p ${DEST_DIR}/covers/jpeg
tar -xf source/covers/jpegs-android.tar -C ${DEST_DIR}/covers/jpeg/
cp -f source/CLICodec.py.android ${DEST_DIR}/CLICodec.py
cp -f source/IOManager.py.android ${DEST_DIR}/IOManager.py
cp -f source/wordlist.txt ${DEST_DIR}/wordlist.txt
cp -f source/phrases.txt ${DEST_DIR}/phrases.txt
cp -f source/pixelfed/whiteboard.json.pixelfed ${DEST_DIR}/whiteboard.json
cp -f source/pixelfed/whiteboard.stealth.json.pixelfed ${DEST_DIR}/whiteboard.stealth.json


formatlog "INFO" "Moving Linux arm64 Client Files (Nothing to Build)"
DEST_DIR="${BASE_DIR}/pixelfed-plugin/artifacts/linux-arm64-v8a-client/DestiniPixelfed"
mkdir -p ${DEST_DIR}
cp -rf source/*.py ${DEST_DIR}
cp -rf source/pixelfed/*.py ${DEST_DIR}
mkdir -p ${DEST_DIR}/scripts
cp source/scripts/common/* ${DEST_DIR}/scripts 
cp -f source/scripts/pixelfed/* ${DEST_DIR}/scripts 
cp -rf source/pixelfed/manifest.pixelfed.json ${DEST_DIR}/manifest.json
cp -rf source/auth.json ${DEST_DIR}/auth.json
cp -rf source/bin ${DEST_DIR}
cp -rf source/bin-linux-arm64/* ${DEST_DIR}/bin/
mkdir -p ${DEST_DIR}/libs
cp -rf source/libs-linux-arm64/*.so ${DEST_DIR}/libs
mkdir -p ${DEST_DIR}/covers
cp -f source/covers/jpegs.tar ${DEST_DIR}/covers/jpegs.tar
cp -f source/wordlist.txt ${DEST_DIR}/wordlist.txt
cp -f source/phrases.txt ${DEST_DIR}/phrases.txt
cp -f source/pixelfed/whiteboard.json.pixelfed ${DEST_DIR}/whiteboard.json
cp -f source/pixelfed/whiteboard.stealth.json.pixelfed ${DEST_DIR}/whiteboard.stealth.json


formatlog "INFO" "Moving Linux arm64 Server Files (Nothing to Build)"
DEST_DIR="${BASE_DIR}/pixelfed-plugin/artifacts/linux-arm64-v8a-server/DestiniPixelfed"
mkdir -p ${DEST_DIR}
cp -rf source/*.py ${DEST_DIR}
cp -rf source/pixelfed/*.py ${DEST_DIR}
mkdir -p ${DEST_DIR}/scripts
cp source/scripts/common/* ${DEST_DIR}/scripts 
cp -f source/scripts/pixelfed/* ${DEST_DIR}/scripts 
cp -rf source/pixelfed/manifest.pixelfed.json ${DEST_DIR}/manifest.json
cp -rf source/auth.json ${DEST_DIR}/auth.json
cp -rf source/bin ${DEST_DIR}
cp -rf source/bin-linux-arm64/* ${DEST_DIR}/bin/
mkdir -p ${DEST_DIR}/libs
cp -rf source/libs-linux-arm64/*.so ${DEST_DIR}/libs
mkdir -p ${DEST_DIR}/covers
cp -f source/covers/jpegs.tar ${DEST_DIR}/covers/jpegs.tar
cp -f source/wordlist.txt ${DEST_DIR}/wordlist.txt
cp -f source/phrases.txt ${DEST_DIR}/phrases.txt
cp -f source/pixelfed/whiteboard.json.pixelfed ${DEST_DIR}/whiteboard.json
cp -f source/pixelfed/whiteboard.stealth.json.pixelfed ${DEST_DIR}/whiteboard.stealth.json




formatlog "INFO" "Moving Android Client Files (Nothing to Build)"
DEST_DIR="${BASE_DIR}/pixelfed-plugin/artifacts/android-x86_64-client/DestiniPixelfed"
mkdir -p ${DEST_DIR}
cp -rf source/*.py ${DEST_DIR}
cp -rf source/pixelfed/*.py ${DEST_DIR}
mkdir -p ${DEST_DIR}/scripts
cp source/scripts/common/* ${DEST_DIR}/scripts
# Renaming to jel2_Pixelfed_codec_android.sh
cp -f source/scripts/pixelfed/jel2_Pixelfed_codec_android_x86.sh ${DEST_DIR}/scripts/jel2_Pixelfed_codec_android.sh
cp -rf source/pixelfed/manifest.pixelfed.json ${DEST_DIR}/manifest.json
cp -rf source/auth.json ${DEST_DIR}/auth.json
cp -rf source/bin ${DEST_DIR}
mkdir -p ${DEST_DIR}/libs
cp -rf source/libs/android/*.so ${DEST_DIR}/libs
rm -rf ${DEST_DIR}/covers
mkdir -p ${DEST_DIR}/covers/jpeg
tar -xf source/covers/jpegs-android.tar -C ${DEST_DIR}/covers/jpeg/
cp -f source/covers/jpegs.tar ${DEST_DIR}/covers/jpegs.tar
cp -f source/CLICodec.py.android ${DEST_DIR}/CLICodec.py
cp -f source/IOManager.py.android ${DEST_DIR}/IOManager.py
cp -f source/wordlist.txt ${DEST_DIR}/wordlist.txt
cp -f source/phrases.txt ${DEST_DIR}/phrases.txt
cp -f source/pixelfed/whiteboard.json.pixelfed ${DEST_DIR}/whiteboard.json
cp -f source/pixelfed/whiteboard.stealth.json.pixelfed ${DEST_DIR}/whiteboard.stealth.json





formatlog "INFO" "Moving Linux Client Files (Nothing to Build)"
DEST_DIR="${BASE_DIR}/pixelfed-plugin/artifacts/linux-x86_64-client/DestiniPixelfed"
mkdir -p ${DEST_DIR}
cp source/*.py ${DEST_DIR}
cp -rf source/pixelfed/*.py ${DEST_DIR}
mkdir -p ${DEST_DIR}/scripts
cp source/scripts/common/* ${DEST_DIR}/scripts
cp -f source/scripts/pixelfed/* ${DEST_DIR}/scripts
cp -rf source/pixelfed/manifest.pixelfed.json ${DEST_DIR}/manifest.json
cp -rf source/bin ${DEST_DIR}
cp -rf source/libs ${DEST_DIR}
mkdir -p ${DEST_DIR}/covers
cp -f source/covers/jpegs.tar ${DEST_DIR}/covers/jpegs.tar
cp -f source/wordlist.txt ${DEST_DIR}/wordlist.txt
cp -f source/phrases.txt ${DEST_DIR}/phrases.txt
cp -f source/pixelfed/whiteboard.json.pixelfed ${DEST_DIR}/whiteboard.json
cp -f source/pixelfed/whiteboard.stealth.json.pixelfed ${DEST_DIR}/whiteboard.stealth.json
			       
				


formatlog "INFO" "Moving Linux Server Files (Nothing to Build)" 
DEST_DIR="${BASE_DIR}/pixelfed-plugin/artifacts/linux-x86_64-server/DestiniPixelfed"
mkdir -p ${DEST_DIR}
cp -rf source/*.py ${DEST_DIR}
cp -rf source/pixelfed/*.py ${DEST_DIR}
mkdir -p ${DEST_DIR}/scripts
cp source/scripts/common/* ${DEST_DIR}/scripts
cp -f source/scripts/pixelfed/* ${DEST_DIR}/scripts 
cp -rf source/pixelfed/manifest.pixelfed.json ${DEST_DIR}/manifest.json
cp -rf source/bin ${DEST_DIR}
cp -rf source/libs ${DEST_DIR}
mkdir -p ${DEST_DIR}/covers
cp -f source/covers/jpegs.tar ${DEST_DIR}/covers/jpegs.tar
cp -f source/wordlist.txt ${DEST_DIR}/wordlist.txt
cp -f source/phrases.txt ${DEST_DIR}/phrases.txt
cp -f source/pixelfed/whiteboard.json.pixelfed ${DEST_DIR}/whiteboard.json
cp -f source/pixelfed/whiteboard.stealth.json.pixelfed ${DEST_DIR}/whiteboard.stealth.json



echo "DONE"
