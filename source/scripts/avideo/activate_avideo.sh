#!/usr/bin/env bash
# -----------------------------------------------------------------------------
# Start internal (running in a RACE node) services
#
# Note: For Two Six COMMS Plugin, there are no internal requirements. will print
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



if [ -f /tmp/avideo_init ]; then
    exit 0
fi

mkdir -p /ramfs/destini/.cover
mkdir -p /ramfs/destini/covers/jpeg
mkdir -p /ramfs/destini/covers/video

chmod a+x /usr/local/lib/race/comms/DestiniAvideo/bin/*
chmod a+x /usr/local/lib/race/comms/DestiniAvideo/scripts/*
touch /tmp/avideo_init

mkdir -p /ramfs/destiniAvideo
cd /ramfs/destiniAvideo

cp /usr/local/lib/race/comms/DestiniAvideo/covers/jpegs.tar /ramfs/destini/covers/jpeg
cp /usr/local/lib/race/comms/DestiniAvideo/covers/videos.tar /ramfs/destini/covers/video

cd /ramfs/destini/covers/jpeg

tar -xf jpegs.tar

cd /ramfs/destini/covers/video

tar -xf videos.tar

#ln -s /aux_data/DestiniAvideo/destini-comms/covers covers
#ln -s /aux_data/DestiniAvideo/destini-comms/.cover .cover


find . -type d -exec chmod o+rx {} \;
find . -type f -exec chmod o+r {} \;


