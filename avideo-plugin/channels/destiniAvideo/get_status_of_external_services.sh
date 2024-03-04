#!/usr/bin/env bash
# -----------------------------------------------------------------------------
# Get status of external (not running in a RACE node) services required by channel.
# Intent is to ensure that the channel will be functional if a RACE deployment
# were to be started and connections established
#
# Note: For Two Six Indirect Links, need to check the status of the two six whiteboard
#
# Arguments:
# -h, --help
#     Print help and exit
#
# Example Call:
#    bash get_status_of_external_services.sh \
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
        echo "Example Call: bash get_status_of_external_services.sh"
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


formatlog "INFO" "Getting compose status. avideo-db, sqladmin, encoder, race.example1 must be healthy" 
docker-compose -p pixelfed-whiteboard -f "${BASE_DIR}/docker-compose-avideo.yml" ps

formatlog "INFO" "Getting Expected Container Statuses. race.example1, encoder, sqladmin, avideo-db need to be running"
# TODO, once we have health checks, we need to add '--filter "health=healthy"' to the status commands

DB_RUNNING=$(docker ps -q --filter "name=avideo-redis-whiteboard" --filter "status=running")

if [ -z "${DB_RUNNING}" ]; then
    echo "Avideo Redis Whiteboard is not running, Exit 1"
    exit 1
fi

APP_RUNNING=$(docker ps -q --filter "name=avideo-redis" --filter "status=running")

if [ -z "${APP_RUNNING}" ]; then
    echo "Avideo Redis is not running, Exit 1"
    exit 1
fi


echo "All expected services are running"


