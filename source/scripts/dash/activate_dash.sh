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


function _dash_init()
{

    if [ -f /tmp/dash_init ]; then
	exit 0
    fi

    chmod a+x /usr/local/lib/race/comms/DestiniDash/bin/*
    chmod a+x /usr/local/lib/race/comms/DestiniDash/scripts/*

    touch /tmp/dash_init

    #mkdir -p /ramfs/destiniDash
    #mkdir -p /ramfs/destiniDash
    mkdir -p /ramfs/destini
    mkdir -p /ramfs/destini/steg/dash
    mkdir -p /ramfs/destini/steg/jpeg
    mkdir -p /ramfs/destini/.cover
    mkdir -p /ramfs/destini/covers/jpeg
    mkdir -p /ramfs/destini/covers/dash


    #cd /ramfs

    #ln -s /aux_data/DestiniDash/destini-comms/covers /ramfs/destiniDash/covers
    #ln -s /aux_data/DestiniDash/destini-comms/.cover /ramfs/destiniDash/.cover

    # is this creating /ramfs/ramfs/destiniDash ???
    
    #change this tar to jpeg.tar, to copy the wanted jpegs over
    #cp /usr/local/lib/race/comms/DestiniDash/covers/destini.tar /ramfs/destiniDash
    cp /usr/local/lib/race/comms/DestiniDash/covers/jpegs.tar /ramfs/destini/covers/jpeg
    cp /usr/local/lib/race/comms/DestiniDash/covers/videos.tar /ramfs/destini/covers/dash

    #add in a dash_video.tar, to copy the wanted videos over

    #this doesn't seem to currently do anything, due to nothing being there
    #cat /ramfs/destiniDash/covers/jpeg/capacities.txt | sed -e 's/\-comms/Dash/g' > /ramfs/destiniDash/steg/jpeg/capacities.txt

    #cd /ramfs/destiniDash
    cd /ramfs/destini/covers/jpeg
    #tar -xf destini.tar
    tar -xf jpegs.tar
    #cp /ramfs/destiniDash/covers/jpeg/ /ramfs/destiniDash/steg/jpeg
    cd /ramfs/destini/covers/dash

    tar -xf videos.tar
    
    #this is to fix the hardcoding failure during server startup
    #where it looks for a few specific video files to exist
    touch crows1_320.mp4

    #This didn't work, need to properly add it to the path
    #export PATH=$PATH:/usr/local/lib/race/comms/DestiniDash/bin

    find /ramfs/destini -type d -exec chmod o+rx {} \;
    find /ramfs/destini -type f -exec chmod o+r {} \;
    #find destiniDash -type d -exec chmod o+rx {} \;
    #find destiniDash -type f -exec chmod o+r {} \;

}

function _nginx_activate()
{
    nginx_cnt=`pgrep nginx |wc -l`
    #sed -i 's/destini\-comms/destini/g' /usr/local/conf/nginx.conf
    #sed -i 's/destini\-comms/destiniDash/g' /usr/local/nginx/conf/nginx.conf
    
    if [ $nginx_cnt == 0 ]; then
	cd /usr/local/lib/race/comms/DestiniDash/scripts
    fi
    
}

case $1 in
    init)
	_dash_init
	;;
    activate)
	_nginx_activate
	;;
esac
      
