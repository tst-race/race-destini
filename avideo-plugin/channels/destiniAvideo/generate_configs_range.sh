#!/usr/bin/env bash
# -----------------------------------------------------------------------------
# Generate configs for the plugin
#
#    bash generate_configs.sh {arguments}
# -----------------------------------------------------------------------------


set -e


###
# Arguments
###


# Get Path
BASE_DIR=$(cd $(dirname ${BASH_SOURCE[0]}) >/dev/null 2>&1 && pwd)


###
# Main Execution
###


python3 ${BASE_DIR}/generate_configs.py "$@"
python3 ${BASE_DIR}/gen_whiteboard.py --channel=Avideo "$@"

