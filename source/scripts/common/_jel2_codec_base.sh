# This file must be source'd and _not directly invoked_.

# Based upon jel2_Pixelfed_codec.sh

# Optional configuration symbols
#
#   TMP          location of log and temporary files; default: /tmp
#   KEEPTMP      if non-empty, do not remove "$TMP" files
#   LOGOUT       log re-direction command; default: "> /dev/null 2>&1"
#   WEDGE        base name of wedge app (e.g., pix_wedge, wedge.android, etc.); default: pix_wedge
#   UNWEDGE      base name of unwedge app (e.g., pix_unwedge, unwedge.android, etc.); default: pix_unwedge
#   JPEGOPTIM    if non-empty, invoke jpegoptim
#   JPEG45QUAL   if non-empty, reduce JPEG quality to 45
#   JPEGPIXELFED if non-empty, add jpegoptim arguments
#   NOSIZECHECK  if non-empty, skip decode length verification
#   OLDARGS      if non-empty, use old short codec calling sequence
#
# Optional logging functions.  See code below.
#
#   _outlog      log re-direction function; takes as arguments a command line invocation (see default implementation below).
#
# Optional diagnostic functions (primarily used by jel2_Pixelfed_codec_android.sh).  See code below.
#
#   _hello0
#   _hello11
#   _altPaths
#   _hello2
#   _helloEncode
#   _encodeStatus
#

#############
# Functions #
#############

__log ()
{
    echo "$(date): $1" >> "$2"
}

_logEnc ()
{
    __log "$1" "$_wedgeLog"
}

_logDec ()
{
    __log "$1" "$_unwedgeLog"
}

_logError ()
{
    echo "$1" 1>&2
}

if ! type -t "_outlog" > /dev/null; then
_outlog()
{
    $@ > /dev/null 2>&1
}
fi

_usage ()
{
    _logError "$(basename $0) [options...] (encode | decode) ..."
    exit $1
}

_checkApps ()
{
    if [ ! -f "$_wedge" -o ! -f "$_unwedge" ]; then
        _logError 'ERROR: missing $_WEDGE or $_UNWEDGE applications.'
        exit 1
    fi
}

_decode ()
{
    if [ -n "$JPEG45QUAL" ]; then
        # For Pixelfed, reduce the image quality to 45 before invoking
        # unwedge.
        _pDeIdx=2
        local _jqual45="$_TMP/jqual45$$.jpg"

        jpegtopnm "$_jDeIn" | ppmtojpeg -quality 45 > "$_jqual45"
        mv -f "$_jqual45" "$_jDeIn"
    else
        _pDeIdx=0
    fi

    "${_unwedge:-echo}" $@
}

_jpegoptim()
{
    cat <<EOF > $_TMP/$$_resize.php
<?php
\$source = imagecreatefromjpeg(\$argv[1]);
\$destination = imagecreatetruecolor(1440, 1080);
imagecopyresampled (\$destination, \$source, 0, 0, 0, 0, 1440, 1080, 1440, 1080);
imagejpeg(\$destination, \$argv[2], 80);
?>
EOF
    _outlog php $_TMP/$$_resize.php $_jEnOut $_TMP/$$_steg2.jpg
    if [ -n $"JPEGPIXELFED" ]; then
        local _jOptimOpts="-m75 --strip-all --all-progressive"
    fi
    _outlog jpegoptim $_jOptimOpts $_TMP/$$_steg2.jpg
    if [ -n "$JPEG45QUAL" ]; then
        jpegtopnm $_TMP/$$_steg2.jpg > $_TMP/$$_steg2.pnm
        _outlog ppmtojpeg -quality 45 $_TMP/$$_steg2.pnm > $_TMP/$$_steg3.jpg
    fi

    #_logEnc "${@:1:$#-1}"    # everything except last argument

    _outlog "$_unwedge" ${@:1:$#-1} $_TMP/$$_steg2.jpg $_TMP/$$_out.msg
    _outlog diff $_jEnOut $_TMP/$$_out.msg

    if [ $? -ne 0 ]; then
        _status=11
    fi
}

_checkjpegoptim()
{
    # Handle (weird) case where image gets downloaded before jpegoptim is performed
    grep -q "CREATOR: gd-jpeg" "$_jDeIn"
    _status=$?

    if [ $_status -eq 0 ]; then
        _outlog jpegoptim -m75 --strip-all --all-progressive "$_jDeIn"
    fi
}

_checkdecsize()
{
    _fsize=$(stat -c%s "$_jDeOut")
    if [ $_fsize -gt 48 ]; then
        egrep -q '^bJeL' "$_jDeOut"
        _status=$?
    else
        _status=48 # too short
    fi
}

_runFunc()
{
    local _func="$1"

    if type -t "$_func" > /dev/null; then
        $@
    fi
}


########
# Main #
########

_runFunc _hello0

_TMP=${TMP:-/tmp}

if [ -z "$TMP" -a -d "/log" ]; then
    _wedgeLog="/log/wedge.log"
    _unwedgeLog="/log/unwedge.log"
else
    _wedgeLog="$_TMP/wedge.log"
    _unwedgeLog="$_TMP/unwedge.log"
fi

_dirname=$(dirname $0)
export PATH="$_dirname/../bin:$PATH"

_runFunc _hello11

_WEDGE=${WEDGE:-pix_wedge}
_UNWEDGE=${UNWEDGE:-pix_unwedge}

_wedge=$(which $_WEDGE)
_unwedge=$(which $_UNWEDGE)

if [ -z "$_wedge" ]; then
    if type -t _altPaths > /dev/null; then
        _altPaths
    else
        _wedge=$_dirname/$_WEDGE
        _unwedge=$_dirname/$_UNWEDGE
    fi
fi

_runFunc _hello2

_checkApps

# https://unix.stackexchange.com/questions/14270/get-exit-status-of-process-thats-piped-to-another

_cmd=$1; shift

case "$_cmd" in

    encode)
        _jEnIn="$_TMP/jEnIn$$.msg"
        _jEnOut="$_TMP/jEnOut$$.jpg"

        _logEnc "$0 $@"
        cat > "$_jEnIn"

        _runFunc _helloEncode $@
        _logEnc "msgIn: $(wc -c "$_jEnIn") ($_jEnIn)"

        # Encode/embed the non-empty message

        if [ -s "$_jEnIn" ]; then

            if [ -n "$OLDARGS" ]; then
                 cat "$_jEnIn" | "$_wedge" $@ | tee "$_jEnOut"
                _status=${PIPESTATUS[1]}
            else
                _outlog "$_wedge" -data "$_jEnIn" $@ "$_jEnOut"
                _status=$?
            fi

            _runFunc _encodeStatus

            if [ $_status -eq 0 -a -n "$JPEGOPTIM" ]; then
                _jpegoptim $@
            fi

            if [ $_status -eq 0 ]; then
                cat $_jEnOut
                _logEnc "msgOut: $(wc -c "$_jEnOut") ($_jEnOut)"
            fi

    	# Accommodate empty message

    	else
    	    _jCover="${@:$#}"
    	    cat $_jCover
    	    _status=$?
            _logEnc "coverOut: ($_jCover)"
    	fi

        if [ -z "$KEEPTMP" ]; then
            rm -f $_TMP/$$_* $_jEnIn $_jEnOut
        fi

        cat << EOF >> "$_wedgeLog"
$(date +%c) exit $_status

EOF
        ;;

    decode)
        _jDeIn="$_TMP/jDeIn$$.jpg"
        _jDeOut="$_TMP/jDeOut$$.msg"

        _logDec "$0 $@"

        cat > "$_jDeIn"

        if [ -n "$JPEGOPTIM" ]; then
            _checkjpegoptim
        fi

        if [ -n "$OLDARGS" ]; then
            _decode $@ "$_jDeIn"
            _status=${PIPESTATUS[$_pDeIdx]}
        else
            _outlog _decode $@ "$_jDeIn" "$_jDeOut"
            _status=$?

            if [ $_status -eq 0 -a -z "$NOSIZECHECK" ]; then
                _checkdecsize
            fi

            if [ $_status -eq 0 ]; then
                cat "$_jDeOut"
            fi
        fi

        cat << EOF >> "$_unwedgeLog"
$(date +%c) exit $_status

EOF
        if [ -n "$KEEPTMP" ]; then
            _logDec "  $_jDeIn $_jDeOut"
        else
            rm -f "$_jDeIn" "$_jDeOut"
        fi
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
