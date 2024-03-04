#!/usr/bin/env bash
# -----------------------------------------------------------------------------
# Generate configs for the plugin
#
# Note: For Two Six Direct Links, we call the generate_configs.py script. This
# file is a wrapped to have a standardized bash interface
#
# Example Call:
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



#conf_dir=`echo "$@" |awk -F'config-dir' '{print $2}'|tr -s '=' ' ' |awk '{print $1}'`
#networkmanagerfile=`echo $@ |awk -F'--network-manager-request' '{print $2}' |tr -s "=" ' ' |awk '{print $1}'`

#echo $conf_dir $networkmanagerfile

#mkdir -p $conf_dir
#python3 ${BASE_DIR}/pre-filter.py $networkmanagerfile destiniAvideo > $conf_dir/filtered_requests.json
#newargs=`echo $@ |sed -e 's#'$networkmanagerfile'#'$conf_dir'/filtered_requests.json#g'`

python3 ${BASE_DIR}/generate_configs_avideo.py $@


