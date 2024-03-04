#!/bin/bash

# THIS SCRIPT CONVERTS ONE MP4 (IN THE CURRENT FOLDER AND SUBFOLDER) TO A MULTI-BITRATE VIDEO IN MP4-DASH

# Usage:  to_dash_svr_qp.sh <cover_in> <steg_out> <message_in> <dest_dir> [<seed>]

#=================================================================================

# Recipe:

# Step 1 - use video_wedge (supplied with the jel library) to embed
# steganographic content into an .mp4 file containing video and audio.

# Step 2 - convert the .mp4 audio stream into a separate .m4a file (for
# DASH)

# Step 3 - transcode the .mp4 video stream into N separate streams,
# each of which encodes to a desired bitrate (for DASH).

# Step 4 - Use MP4Box to create a DASH manifest (.mpd file).

# Step 5 - upload the DASH manifest (.mpd) and media files (.m4v,
# .m4a) to the server.

#=================================================================================


# Validation tool:
# http://dashif.org/conformance.html

# Documentation:
# https://tdngan.wordpress.com/2016/11/17/how-to-encode-multi-bitrate-videos-in-mpeg-dash-for-mse-based-media-players/

# Remember to add the following mime-types (uncommented) to .htaccess:
# AddType video/mp4 m4s
# AddType application/dash+xml mpd

# DASH-264 JavaScript Reference Client
# https://github.com/Dash-Industry-Forum/dash.js
# https://github.com/Dash-Industry-Forum/dash.js/wiki

#MYDIR=$(dirname $(readlink -f ${BASH_SOURCE[0]}))
# What's the best thing here??
MYDIR=$(pwd)
SAVEDIR=$(pwd)/.dashout
if [ ! -d $SAVEDIR ]; then
    mkdir $SAVEDIR
fi

# Check programs
if [ -z "$(which ffmpeg)" ]; then
    echo "Error: ffmpeg is not installed"
    exit 1
fi

if [ -z "$(which MP4Box)" ]; then
    echo "Error: MP4Box is not installed"
    exit 1
fi

# Steg embedding strategy: Perform one steg embedding at a quality
# level that will survive the desired bitrates, then convert that
# single embedding into each of the DASH streams.
#
#

c=$(basename "$2") # fullname of the stegged output file
f="${c%.*}" # name without extension

# ffmpeg options:
# -vsync 0 should prevent duplicates or dropped frames.
# -g 15 should cause I frames to appear every 15 frames
#
# wedge options: quality = 81 is good for all the bitrates mentioned
# below.

# The first argument to this script is the name of the original MP4 cover
# video with extension ".mp4".
# The second argument to this script is the name of the MP4 video with
# extension ".mp4".
# The third argument is the message file name.
# The fourth argument is the destination folder.
# The fifth optional argument is the video_wedge seed.

# STEP 1: Use video_wedge to embed steganographic content.  Takes an
# input video named by the first argument and embeds the named message
# (second argument is the message file) in the video, leaves JPEG steg
# frames in a directory named ".wedge", and leaves the audio component
# in ".cover/audio.wav":

# The quality level here was obtained from the rick-qual-1x parameter
# survey.  Encoding at JPEG quality 82 results in 100% recovery for
# the bit rates used for ffmpeg below:

_vw_opts="-seed $5"

echo "Calling video wedge on cover files"
wedge_dir="/log/wedge.${BASHPID}"

#video_wedge -ecc 8 -cover "${1}" -message "${3}" -jpeg_quality 82 $_vw_opts

if [ ${6:-0} -eq 1 ]; then
    /usr/local/lib/race/comms/DestiniDash/scripts/video_wedge -mcudensity 100 -bpf 2 -nfreqs 12 -maxfreqs 12 -cover "${1}" -message "${3}" -jpeg_quality 30 -dir /ramfs/destini -wedge_dir $wedge_dir $_vw_opts
else
    /usr/local/lib/race/comms/DestiniDash/scripts/video_wedge -mcudensity 100 -bpf 1 -nfreqs 12 -maxfreqs 12 -cover "${1}" -message "${3}" -jpeg_quality 30 -dir /ramfs/destini -wedge_dir $wedge_dir $_vw_opts
fi

_mp4_cover_name=`basename "{1}" .mp4`
_cover_frame_dir="/ramfs/destini/.cover/${_mp4_cover_name}"

# With "video_wedge", the steg frames are always created and kept in
# the .wedge subdirectory.  Here, the "-output" flag to video_wedge is
# not provided, because we can simply use the .wedge contents to
# directly create each DASH video stream.

_ff_opts="-y -loglevel error"

# Now reassemble the stegged JPEG frames into MP4s at different bit rates:
#

echo "Converting \"$f\" to multi-bitrate video in MPEG-DASH"

rm -f /tmp/jobfile

# ffmpeg $_ff_opts -i "${f}.mp4" -c:a libfdk_aac -ac 2 -ab 128k -vn "${f}_audio.m4a"

# Step 2:  Construct the audio track for DASH:
if [ -f "${_cover_frame_dir}/audio.wav" ]; then
    echo "ffmpeg $_ff_opts -i \"${_cover_frame_dir}/audio.wav\"  -ac 2 -ab 128k -vn \"${f}_audio.m4a\"" >> /tmp/jobfile
elif [ -f "${f}.mp4" ]; then
    echo "ffmpeg $_ff_opts -i \"${f}.mp4\"  -ac 2 -ab 128k -vn \"${f}_audio.m4a\"" >> /tmp/jobfile
fi

# Step 3: Construct four MP4s at each of the desired bit rates.
# Here, N=3, and the bit rates are selected for 100% recovery:

echo "Creating qp12 mp4"

echo "ffmpeg -vsync 0 $_ff_opts -i \"${wedge_dir}/frame-%04d.jpg\" -c:v libx264 -an -qp 12 -f mp4 \"${f}_qp12.mp4\"" >> /tmp/jobfile

echo "Creating qp10 mp4"

echo "ffmpeg -vsync 0 $_ff_opts -i \"${wedge_dir}/frame-%04d.jpg\" -c:v libx264 -an -qp 10 -f mp4 \"${f}_qp10.mp4\"" >> /tmp/jobfile

echo "Creating qp8 mp4"

echo "ffmpeg -vsync 0 $_ff_opts -i \"${wedge_dir}/frame-%04d.jpg\" -c:v libx264 -an -qp 8 -f mp4 \"${f}_qp08.mp4\"" >> /tmp/jobfile

#echo "Create 2000 bit mp4"
#ffmpeg -vsync 0 $_ff_opts -i ".wedge/frame-%04d.jpg" -c:v libx264 -an -crf 2 -f mp4 "${f}_2000.mp4"

parallel --jobs 8 < /tmp/jobfile

rm -f ffmpeg*log*
rm -rf $wedge_dir

_files="${f}_qp12.mp4 ${f}_qp10.mp4 ${f}_qp08.mp4"
if [ -f "${f}_audio.m4a" ]; then
    _files="$_files ${f}_audio.m4a"
fi

# Package everything up into the SAVEDIR:
mv $_files "$SAVEDIR"

# Step 4: Use MP4Box to construct a manifest that will serve the DASH content:
cd "$SAVEDIR"


echo "Using MP4Box to build the manifest"
MP4Box -dash 2000 -rap -frag-rap -profile onDemand $_files -out "${f}_MP4.mpd"

rm $_files

# Step 5: Copy the video into the server directory (the third argument):
mkdir -p "${4}"
echo mv -f ${f}_*_dashinit.mp4 ${f}_MP4.mpd "${4}"
mv -f ${f}_*_dashinit.mp4 ${f}_MP4.mpd "${4}"
