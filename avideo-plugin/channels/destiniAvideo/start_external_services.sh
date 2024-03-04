#!/usr/bin/env bash
# -----------------------------------------------------------------------------
# Start external (not running in a RACE node) services required by channel 
#
# Note: For Two Six Indirect Links, need to stand up the two six whiteboard. This
# will include running a docker-compose.yml file to up the whiteboard and API
#
# Arguments:
# -h, --help
#     Print help and exit
#
# Example Call:
#    bash start_external_services.sh \
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
        echo "Example Call: bash start_external_services.sh"
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


docker-compose -p avideo-redis-whiteboard -f "${BASE_DIR}/docker-compose-redis.yml" up -d

#cnt=`docker logs race.example1 |& grep fork |wc -l`

#while [ $cnt -lt 1 ]
#do
#   echo "Waiting for avideo container to create accounts and initialize..."
#   sleep 10
#   cnt=`docker logs race.example1 |& grep fork |wc -l`
#done

#docker exec avideo-db mysql -pRaceDeeBeeP -e "SET global max_connections=10002"




