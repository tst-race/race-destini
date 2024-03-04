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

rm -rf ${CURRENT_DIR}/avideo-plugin/artifacts/android-arm64-v8a-client/*
rm -rf ${CURRENT_DIR}/avideo-plugin/artifacts/linux-arm64-8va-client/*
rm -rf ${CURRENT_DIR}/avideo-plugin/artifacts/linux-arm64-8va-server/*
rm -rf ${CURRENT_DIR}/avideo-plugin/artifacts/android-x86_64-client/*
rm -rf ${CURRENT_DIR}/avideo-plugin/artifacts/linux-x86_64-client/*
rm -rf ${CURRENT_DIR}/avideo-plugin/artifacts/linux-x86_64-server/*


#formatlog "INFO" "Moving Android Client Files (Nothing to Build)"
#DEST_DIR="${BASE_DIR}/plugin/artifacts/android-client/PluginCommsDestiniAvideo"
#mkdir ${DEST_DIR}
#cp -rf source/* ${DEST_DIR}


formatlog "INFO" "Moving Linux arm64 Client Files (Nothing to Build)"
DEST_DIR="${BASE_DIR}/avideo-plugin/artifacts/linux-arm64-v8a-client/DestiniAvideo"
mkdir -p ${DEST_DIR}
cp -rf source/*.py ${DEST_DIR}
cp -rf source/avideo/*.py ${DEST_DIR}
mkdir -p ${DEST_DIR}/scripts
cp -r source/scripts/common/* ${DEST_DIR}/scripts 
cp -f source/scripts/avideo/* ${DEST_DIR}/scripts
cp -rf source/avideo/manifest.avideo.json ${DEST_DIR}/manifest.json
#cp -rf source/avideo/aux_data*.json ${DEST_DIR}
cp -rf source/bin ${DEST_DIR}
cp -rf source/bin-linux-arm64/* ${DEST_DIR}/bin/
cp -rf source/libs ${DEST_DIR}
mkdir -p ${DEST_DIR}/libs
cp -rf source/libs-linux-arm64/*.so ${DEST_DIR}/libs
mkdir -p ${DEST_DIR}/covers
cp -f source/covers/jpegs.tar ${DEST_DIR}/covers/jpegs.tar
cp -f source/covers/videos.tar ${DEST_DIR}/covers/videos.tar
cp -f source/wordlist.txt ${DEST_DIR}/wordlist.txt
cp -f source/phrases.txt ${DEST_DIR}/phrases.txt
cp -f source/avideo/whiteboard.json.avideo ${DEST_DIR}/whiteboard.json
cp -f source/avideo/whiteboard.stealth.json.avideo ${DEST_DIR}/whiteboard.stealth.json

#need to add source/libs-linux-arm64
				


formatlog "INFO" "Moving Linux arm64 Server Files (Nothing to Build)" 
DEST_DIR="${BASE_DIR}/avideo-plugin/artifacts/linux-arm64-v8a-server/DestiniAvideo"
mkdir -p ${DEST_DIR}
cp -rf source/*.py ${DEST_DIR}
cp -rf source/avideo/*.py ${DEST_DIR}
mkdir -p ${DEST_DIR}/scripts
cp -r source/scripts/common/* ${DEST_DIR}/scripts
cp -f source/scripts/avideo/* ${DEST_DIR}/scripts 
cp -rf source/avideo/manifest.avideo.json ${DEST_DIR}/manifest.json
#cp -rf source/avideo/aux_data*.json ${DEST_DIR}
cp -rf source/bin ${DEST_DIR}
cp -rf source/bin-linux-arm64/* ${DEST_DIR}/bin/
cp -rf source/libs ${DEST_DIR}
mkdir -p ${DEST_DIR}/libs
cp -rf source/libs-linux-arm64/*.so ${DEST_DIR}/libs
mkdir -p ${DEST_DIR}/covers
cp -f source/covers/jpegs.tar ${DEST_DIR}/covers/jpegs.tar
cp -f source/covers/videos.tar ${DEST_DIR}/covers/videos.tar
#cp -rf source/covers ${DEST_DIR}
#cp -f source/bin/wedge.phase2r1 ${DEST_DIR}/bin/wedge
#cp -f source/bin/unwedge.phase2r1 ${DEST_DIR}/bin/unwedge
cp -f source/wordlist.txt ${DEST_DIR}/wordlist.txt
cp -f source/phrases.txt ${DEST_DIR}/phrases.txt
cp -f source/avideo/whiteboard.json.avideo ${DEST_DIR}/whiteboard.json
cp -f source/avideo/whiteboard.stealth.json.avideo ${DEST_DIR}/whiteboard.stealth.json




formatlog "INFO" "Moving Linux Client Files (Nothing to Build)"
DEST_DIR="${BASE_DIR}/avideo-plugin/artifacts/linux-x86_64-client/DestiniAvideo"
mkdir -p ${DEST_DIR}
cp -rf source/*.py ${DEST_DIR}
cp -rf source/avideo/*.py ${DEST_DIR}
mkdir -p ${DEST_DIR}/scripts
cp -r source/scripts/common/* ${DEST_DIR}/scripts 
cp -f source/scripts/avideo/* ${DEST_DIR}/scripts
cp -rf source/avideo/manifest.avideo.json ${DEST_DIR}/manifest.json
#cp -rf source/avideo/aux_data*.json ${DEST_DIR}
cp -rf source/bin ${DEST_DIR}
cp -rf source/libs ${DEST_DIR}
mkdir -p ${DEST_DIR}/covers
cp -f source/covers/jpegs.tar ${DEST_DIR}/covers/jpegs.tar
cp -f source/covers/videos.tar ${DEST_DIR}/covers/videos.tar
cp -f source/wordlist.txt ${DEST_DIR}/wordlist.txt
cp -f source/phrases.txt ${DEST_DIR}/phrases.txt
cp -f source/avideo/whiteboard.json.avideo ${DEST_DIR}/whiteboard.json
cp -f source/avideo/whiteboard.stealth.json.avideo ${DEST_DIR}/whiteboard.stealth.json

				


formatlog "INFO" "Moving Linux Server Files (Nothing to Build)" 
DEST_DIR="${BASE_DIR}/avideo-plugin/artifacts/linux-x86_64-server/DestiniAvideo"
mkdir -p ${DEST_DIR}
cp -rf source/*.py ${DEST_DIR}
cp -rf source/avideo/*.py ${DEST_DIR}
mkdir -p ${DEST_DIR}/scripts
cp -r source/scripts/common/* ${DEST_DIR}/scripts
cp -f source/scripts/avideo/* ${DEST_DIR}/scripts 
cp -rf source/avideo/manifest.avideo.json ${DEST_DIR}/manifest.json
#cp -rf source/avideo/aux_data*.json ${DEST_DIR}
cp -rf source/bin ${DEST_DIR}
cp -rf source/libs ${DEST_DIR}
mkdir -p ${DEST_DIR}/covers
cp -f source/covers/jpegs.tar ${DEST_DIR}/covers/jpegs.tar
cp -f source/covers/videos.tar ${DEST_DIR}/covers/videos.tar
#cp -rf source/covers ${DEST_DIR}
#cp -f source/bin/wedge.phase2r1 ${DEST_DIR}/bin/wedge
#cp -f source/bin/unwedge.phase2r1 ${DEST_DIR}/bin/unwedge
cp -f source/wordlist.txt ${DEST_DIR}/wordlist.txt
cp -f source/phrases.txt ${DEST_DIR}/phrases.txt
cp -f source/avideo/whiteboard.json.avideo ${DEST_DIR}/whiteboard.json
cp -f source/avideo/whiteboard.stealth.json.avideo ${DEST_DIR}/whiteboard.stealth.json



echo "DONE"
