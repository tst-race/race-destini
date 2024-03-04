#!/bin/bash

__log ()
{
    echo "$(date): $1" >> "$2"
}

_logEnc ()
{
    __log "$1" /tmp/wedge.log
}

_logDec ()
{
    __log "$1" /tmp/unwedge.log
}

_logError ()
{
    echo "$1" 1>&2
}

_usage ()
{
    _logError "$(basename $0) [options...] (encode | decode) ..."
    exit $1
}

_checkApps ()
{
    if [ ! -f "$_wedge" ] || [ ! -f "$_unwedge" ]; then
        _logError 'ERROR: missing wedge or unwedge applications.'
        exit 1
    fi
}

if [ "$(basename $0)" == "jel2_Pixelfed_codec.sh" ]; then
_pDeIdx=2
_decode ()
{
    # For Pixelfed, reduce the image quality to 45 before invoking
    # unwedge.

    jpegtopnm | \
    ppmtojpeg -quality 45 | \
    "${_unwedge:-echo}" $*
}
else
_pDeIdx=0
_decode ()
{
    "${_unwedge:-echo}" $*
}
fi

_wedge=$(which wedge)
_unwedge=$(which unwedge)

if [ -z "$_wedge" ]; then
    _dirname=$(dirname $0)
    _wedge=$_dirname/wedge
    _unwedge=$_dirname/unwedge
fi

_checkApps

_cmd=$1; shift

# https://unix.stackexchange.com/questions/14270/get-exit-status-of-process-thats-piped-to-another

case "$_cmd" in

    encode)
        _logEnc "$0 $*"

        "$_wedge" $*
        _status=$?
        cat << EOF >> /tmp/wedge.log
exit $_status

EOF
        ;;

    decode)
        _jDeIn="/tmp/jDeIn$$.jpg"

        _logDec "$0 $*"

        cat > "$_jDeIn"

        _decode $* "$_jDeIn"
        _status=${PIPESTATUS[$_pDeIdx]}
        cat << EOF >> /tmp/unwedge.log
exit $_status

EOF
        rm -f "$_jDeIn"
        ;;

    -h|--help)
        _usage 0
        ;;

    *)
        _logError "ERROR: missing or unrecognized command: \"$_cmd\""
        _usage 1
        ;;
esac

exit $_status
