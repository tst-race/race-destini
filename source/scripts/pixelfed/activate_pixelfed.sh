#!/usr/bin/env bash
# -----------------------------------------------------------------------------
# Start internal (running in a RACE node) services
#
# Note: For Two Six Comms Plugin, there are no internal requirements. will print
# dummy config as an example and to test mounted artifacts
#
# Arguments:
# -h, --help
#     Print help and exit
#
# Example Call:
#    bash start_internal_services.sh \
#        {--help}
# -----------------------------------------------------------------------------


###
# Helper functions
###


# Load Helper Functions
BASE_DIR=$(cd $(dirname ${BASH_SOURCE[0]}) >/dev/null 2>&1 && pwd)



###
# Main Execution
###




if [ -f /tmp/pixelfed_init ]; then
    exit 0
fi

#    chmod a+x /usr/local/lib/race/comms/DestiniPixelfed/bin/*
#    cp /usr/local/lib/race/comms/DestiniPixelfed/bin/* /usr/local/bin/
#    cd /usr/local/lib/race/comms/DestiniPixelfed/scripts/
#    chmod a+x *

touch /tmp/pixelfed_init
chmod a+x /usr/local/lib/race/comms/DestiniPixelfed/bin/*
chmod a+x /usr/local/lib/race/comms/DestiniPixelfed/scripts/*


mkdir -p /ramfs/destini
mkdir -p /ramfs/destini/steg/jpeg
mkdir -p /ramfs/destini/.cover
mkdir -p /ramfs/destini/covers/jpeg


cp /usr/local/lib/race/comms/DestiniPixelfed/covers/jpegs.tar /ramfs/destini/covers/jpeg
cd /ramfs/destini/covers/jpeg
tar -xf jpegs.tar
find . -type d -exec chmod o+rx {} \;
find . -type f -exec chmod o+r {} \;

