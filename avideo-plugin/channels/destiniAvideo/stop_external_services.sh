#!/usr/bin/env bash
# -----------------------------------------------------------------------------
# Stop external (not running in a RACE node) services required by channel
#
# Note: For Two Six Indirect Links, need to tear down the two six whiteboard. This
# will include running a docker-compose.yml file. 
#
# TODO: Do we want to clear state?
#
# Arguments:
# -h, --help
#     Print help and exit
#
# Example Call:
#    bash stop_external_services.sh \
#        {--help}
# -----------------------------------------------------------------------------


###
# Helper functions
###


# Load Helper Functions
BASE_DIR=$(cd $(dirname ${BASH_SOURCE[0]}) >/dev/null 2>&1 && pwd)
. ${BASE_DIR}/helper_functions.sh


###
# Arguments
###


# Parse CLI Arguments
while [ $# -gt 0 ]
do
    key="$1"

    case $key in
        -h|--help)
        echo "Example Call: bash stop_external_services.sh"
        exit 1;
        ;;
        *)
        formatlog "ERROR" "unknown argument \"$1\""
        exit 1
        ;;
    esac
done


###
# Main Execution
###


formatlog "INFO" "Stopping Destini AVideo Service"
docker-compose -p avideo-redis-whiteboard -f ${BASE_DIR}/docker-compose-redis.yml down
#docker-compose -p destini-avideo-wb -f ${BASE_DIR}/docker-compose-avideo.yml down
