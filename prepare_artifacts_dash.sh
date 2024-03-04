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

rm -rf ${CURRENT_DIR}/dash-plugin/artifacts/android-arm64-v8a-client/*
rm -rf ${CURRENT_DIR}/dash-plugin/artifacts/linux-arm64-8va-client/*
rm -rf ${CURRENT_DIR}/dash-plugin/artifacts/linux-arm64-8va-server/*
rm -rf ${CURRENT_DIR}/dash-plugin/artifacts/android-x86_64-client/*
rm -rf ${CURRENT_DIR}/dash-plugin/artifacts/linux-x86_64-client/*
rm -rf ${CURRENT_DIR}/dash-plugin/artifacts/linux-x86_64-server/*

#formatlog "INFO" "Moving Android Client Files (Nothing to Build)"
#DEST_DIR="${BASE_DIR}/plugin/artifacts/android-client/PluginCommsDestiniDash"
#mkdir ${DEST_DIR}
#cp -rf source/* ${DEST_DIR}


# formatlog "INFO" "Moving Linux Client Files (Nothing to Build)"
# DEST_DIR="${BASE_DIR}/dash-plugin/artifacts/linux-x86_64-client/DestiniDash"
# mkdir -p ${DEST_DIR}
# cp -rf source/*.py ${DEST_DIR}
# cp -rf source/scripts ${DEST_DIR}
# cp -rf source/manifest.dash.json ${DEST_DIR}/manifest.json
# cp -rf source/bin ${DEST_DIR}
# cp -rf source/libs ${DEST_DIR}
# cp -rf source/covers ${DEST_DIR}			       


formatlog "INFO" "Moving Android arm64 Client Files (Nothing to Build)"
DEST_DIR="${BASE_DIR}/dash-plugin/artifacts/android-arm64-v8a-client/DestiniDash"
mkdir -p ${DEST_DIR}
cp -rf source/*.py ${DEST_DIR}
cp -rf source/pixelfed/*.py ${DEST_DIR}
cp -rf source/dash/*.py ${DEST_DIR}
mkdir -p ${DEST_DIR}/scripts
cp source/scripts/common/* ${DEST_DIR}/scripts 
cp -f source/scripts/pixelfed/* ${DEST_DIR}/scripts 
cp -f source/scripts/dash/* ${DEST_DIR}/scripts
cp -rf source/dash/manifest.dash.json ${DEST_DIR}/manifest.json
#cp -rf source/dash/aux_data*.json ${DEST_DIR}
cp -rf source/auth.json ${DEST_DIR}/auth.json
cp -rf source/bin ${DEST_DIR}
mkdir -p ${DEST_DIR}/libs
cp -rf source/libs/arm64/*.so ${DEST_DIR}/libs
mkdir -p ${DEST_DIR}/covers
cp -f source/CLICodec.py.android ${DEST_DIR}/CLICodec.py
cp -f source/IOManager.py.android ${DEST_DIR}/IOManager.py
cp -f source/wordlist.txt ${DEST_DIR}/wordlist.txt
cp -f source/phrases.txt ${DEST_DIR}/phrases.txt
cp -f source/dash/whiteboard.json.dash ${DEST_DIR}/whiteboard.json




formatlog "INFO" "Moving Linux arm64 Client Files (Nothing to Build)"
DEST_DIR="${BASE_DIR}/dash-plugin/artifacts/linux-arm64-v8a-client/DestiniDash"
mkdir -p ${DEST_DIR}
cp -rf source/*.py ${DEST_DIR}
cp -rf source/pixelfed/*.py ${DEST_DIR}
cp -rf source/dash/*.py ${DEST_DIR}
mkdir -p ${DEST_DIR}/scripts
cp source/scripts/common/* ${DEST_DIR}/scripts 
cp -f source/scripts/pixelfed/* ${DEST_DIR}/scripts 
cp -f source/scripts/dash/* ${DEST_DIR}/scripts 
cp -rf source/dash/manifest.dash.json ${DEST_DIR}/manifest.json
#cp -rf source/dash/aux_data*.json ${DEST_DIR}
cp -rf source/auth.json ${DEST_DIR}/auth.json
cp -rf source/bin ${DEST_DIR}
cp -rf source/bin-linux-arm64/* ${DEST_DIR}/bin/
mkdir -p ${DEST_DIR}/libs
cp -rf source/libs-linux-arm64/*.so ${DEST_DIR}/libs
mkdir -p ${DEST_DIR}/covers
cp -f source/covers/jpegs.tar ${DEST_DIR}/covers/jpegs.tar
#need to add dash.tar for videos here
cp -f source/covers/videos.tar ${DEST_DIR}/covers/videos.tar
cp -f source/wordlist.txt ${DEST_DIR}/wordlist.txt
cp -f source/phrases.txt ${DEST_DIR}/phrases.txt
cp -f source/dash/whiteboard.json.dash ${DEST_DIR}/whiteboard.json




formatlog "INFO" "Moving Linux arm64 Server Files (Nothing to Build)"
DEST_DIR="${BASE_DIR}/dash-plugin/artifacts/linux-arm64-v8a-server/DestiniDash"
mkdir -p ${DEST_DIR}
cp -rf source/*.py ${DEST_DIR}
cp -rf source/pixelfed/*.py ${DEST_DIR}
cp -rf source/dash/*.py ${DEST_DIR}
mkdir -p ${DEST_DIR}/scripts
cp source/scripts/common/* ${DEST_DIR}/scripts 
cp -f source/scripts/pixelfed/* ${DEST_DIR}/scripts 
cp -f source/scripts/dash/* ${DEST_DIR}/scripts
cp -rf source/dash/manifest.dash.json ${DEST_DIR}/manifest.json
#cp -rf source/dash/aux_data*.json ${DEST_DIR}
cp -rf source/auth.json ${DEST_DIR}/auth.json
cp -rf source/bin ${DEST_DIR}
cp -rf source/bin-linux-arm64/* ${DEST_DIR}/bin/
mkdir -p ${DEST_DIR}/libs
cp -rf source/libs-linux-arm64/*.so ${DEST_DIR}/libs
mkdir -p ${DEST_DIR}/covers
cp -f source/covers/jpegs.tar ${DEST_DIR}/covers/jpegs.tar
#need to add dash.tar for videos here
cp -f source/covers/videos.tar ${DEST_DIR}/covers/videos.tar
cp -f source/wordlist.txt ${DEST_DIR}/wordlist.txt
cp -f source/phrases.txt ${DEST_DIR}/phrases.txt
cp -f source/dash/whiteboard.json.dash ${DEST_DIR}/whiteboard.json




formatlog "INFO" "Moving Android Client Files (Nothing to Build)"
DEST_DIR="${BASE_DIR}/dash-plugin/artifacts/android-x86_64-client/DestiniDash"
mkdir -p ${DEST_DIR}
cp -rf source/*.py ${DEST_DIR}
cp -rf source/pixelfed/*.py ${DEST_DIR}
cp -rf source/dash/*.py ${DEST_DIR}
mkdir -p ${DEST_DIR}/scripts
cp source/scripts/common/* ${DEST_DIR}/scripts
cp -f source/scripts/pixelfed/* ${DEST_DIR}/scripts
cp -f source/scripts/dash/* ${DEST_DIR}/scripts
cp -rf source/dash/manifest.dash.json ${DEST_DIR}/manifest.json
#cp -rf source/dash/aux_data*.json ${DEST_DIR}
cp -rf source/auth.json ${DEST_DIR}/auth.json
cp -rf source/bin ${DEST_DIR}
mkdir -p ${DEST_DIR}/libs
cp -rf source/libs/android/*.so ${DEST_DIR}/libs
mkdir -p ${DEST_DIR}/covers
cp -f source/CLICodec.py.android ${DEST_DIR}/CLICodec.py
cp -f source/IOManager.py.android ${DEST_DIR}/IOManager.py
cp -f source/wordlist.txt ${DEST_DIR}/wordlist.txt
cp -f source/phrases.txt ${DEST_DIR}/phrases.txt
cp -f source/dash/whiteboard.json.dash ${DEST_DIR}/whiteboard.json




formatlog "INFO" "Moving Linux Client Files (Nothing to Build)"
DEST_DIR="${BASE_DIR}/dash-plugin/artifacts/linux-x86_64-client/DestiniDash"
mkdir -p ${DEST_DIR}
cp source/*.py ${DEST_DIR}
cp -rf source/pixelfed/*.py ${DEST_DIR}
cp -rf source/dash/*.py ${DEST_DIR}
mkdir -p ${DEST_DIR}/scripts
cp source/scripts/common/* ${DEST_DIR}/scripts
cp -f source/scripts/pixelfed/* ${DEST_DIR}/scripts
cp -f source/scripts/dash/* ${DEST_DIR}/scripts
cp -rf source/dash/manifest.dash.json ${DEST_DIR}/manifest.json
#cp -rf source/dash/aux_data*.json ${DEST_DIR}
cp -rf source/bin ${DEST_DIR}
cp -rf source/libs ${DEST_DIR}
mkdir -p ${DEST_DIR}/covers
cp -f source/covers/jpegs.tar ${DEST_DIR}/covers/jpegs.tar
cp -f source/covers/videos.tar ${DEST_DIR}/covers/videos.tar
#need to add dash.tar for videos here
cp -f source/wordlist.txt ${DEST_DIR}/wordlist.txt
cp -f source/phrases.txt ${DEST_DIR}/phrases.txt
cp -f source/dash/whiteboard.json.dash ${DEST_DIR}/whiteboard.json



#does this one need a /covers and corresponding jpegs and dash tars
formatlog "INFO" "Moving Linux Server Files (Nothing to Build)" 
DEST_DIR="${BASE_DIR}/dash-plugin/artifacts/linux-x86_64-server/DestiniDash"
mkdir -p ${DEST_DIR}
cp -rf source/*.py ${DEST_DIR}
cp -rf source/pixelfed/*.py ${DEST_DIR}
cp -rf source/dash/*.py ${DEST_DIR}
mkdir -p ${DEST_DIR}/scripts
cp source/scripts/common/* ${DEST_DIR}/scripts 
cp -f source/scripts/pixelfed/* ${DEST_DIR}/scripts
cp -f source/scripts/dash/* ${DEST_DIR}/scripts
cp -rf source/dash/manifest.dash.json ${DEST_DIR}/manifest.json
#cp -rf source/dash/aux_data*.json ${DEST_DIR}
cp -rf source/bin ${DEST_DIR}
cp -rf source/libs ${DEST_DIR}
mkdir -p ${DEST_DIR}/covers
cp -f source/covers/jpegs.tar ${DEST_DIR}/covers/jpegs.tar
cp -f source/covers/videos.tar ${DEST_DIR}/covers/videos.tar
#need to add dash.tar for videos here
cp -f source/wordlist.txt ${DEST_DIR}/wordlist.txt
cp -f source/phrases.txt ${DEST_DIR}/phrases.txt
cp -f source/dash/whiteboard.json.dash ${DEST_DIR}/whiteboard.json



echo "DONE"
