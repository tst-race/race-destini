#!/bin/bash

if [ -d "/log" ]; then
    _wedgeLog="/log/wedge.log"
    _unwedgeLog="/log/unwedge.log"
else
    _wedgeLog="/tmp/wedge.log"
    _unwedgeLog="/tmp/unwedge.log"
fi


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

_dirname=$(dirname $0)
export PATH="$_dirname/../bin:$PATH"

if [ "$(basename $0)" == "jel2_Pixelfed_codec.sh" ]; then
_pDeIdx=2
_decode ()
{
    # For Pixelfed, reduce the image quality to 45 before invoking
    # unwedge.

#    jpegtopnm | \
#    ppmtojpeg -quality 45 | \
    "${_unwedge:-echo}" $*
}
else
_pDeIdx=0
_decode ()
{
    "${_unwedge:-echo}" $*
}
fi

#_wedge=$(which pix_wedge)
#_unwedge=$(which pix_unwedge)
_wedge=$(which wedge)
_unwedge=$(which unwedge)

if [ -z "$_wedge" ]; then
    _wedge=$_dirname/wedge
    _unwedge=$_dirname/unwedge
fi

_checkApps

_cmd=$1; shift

# https://unix.stackexchange.com/questions/14270/get-exit-status-of-process-thats-piped-to-another

case "$_cmd" in

    encode)
	_logEnc "$0 $*"
	cat > "/tmp/$$_msgIn"
	_logEnc "msgIn: $(wc -c /tmp/$$_msgIn)"	
        "$_wedge" -data "/tmp/$$_msgIn" $*  "/tmp/$$_steg.jpg" > /dev/null 2>&1
	_status=$?

	if [ $_status -eq 0 ]; then
	    cat <<EOF > /tmp/$$_resize.php
<?php
\$source = imagecreatefromjpeg(\$argv[1]);
\$destination = imagecreatetruecolor(1440, 1080);
imagecopyresampled (\$destination, \$source, 0, 0, 0, 0, 1440, 1080, 1440, 1080); 
imagejpeg(\$destination, \$argv[2], 80);
?>
EOF
	    php /tmp/$$_resize.php /tmp/$$_steg.jpg /tmp/$$_steg2.jpg > /dev/null 2>&1
	    jpegoptim -m75 --strip-all --all-progressive /tmp/$$_steg2.jpg > /dev/null 2>&1
	    #jpegtopnm /tmp/$$_steg2.jpg > /tmp/$$_steg2.pnm
	    #ppmtojpeg -quality 45 /tmp/$$_steg2.pnm > /tmp/$$_steg3.jpg 2>&1
	    #echo "${@:1:$#-1}" >> /tmp/foo.out  #everthing except last argument	    
	    "$_unwedge" ${@:1:$#-1} /tmp/$$_steg2.jpg /tmp/$$_out.msg > /dev/null 2>&1
	    diff /tmp/$$_msgIn /tmp/$$_out.msg > /dev/null 2>&1
	    
	    if [ $? -eq 0 ]; then
		cat /tmp/$$_steg.jpg
	    else
		_status=11
	    fi
	fi

	#rm -f /tmp/$$_*

        cat << EOF >> "$_wedgeLog"
exit $_status

EOF
        ;;

    decode)
        _jDeIn="/tmp/jDeIn$$.jpg"
	_jDeOut="/tmp/jDeOut$$.msg"

        _logDec "$0 $*"

        cat > "$_jDeIn"

	# weird case on image gets downloaded before jpegoptim is performed
	grep -q "CREATOR: gd-jpeg" "$_jDeIn"
	_status=$? 
	
	if [ $_status -eq 0 ]; then
	    jpegoptim -m75 --strip-all --all-progressive "$_jDeIn" > /dev/null 2>&1
	fi

        _decode $* "$_jDeIn" "$_jDeOut" > /dev/null 2>&1
	_status=$?
	
	if [ $_status -eq 0 ]; then
	    _fsize=$(stat -c%s "$_jDeOut")
	    if [ $_fsize -gt 48 ]; then
		egrep -q '^bJeL' "$_jDeOut"
		_status=$?
	    else
		_status=48 # too short
	    fi
 
	    if [ $_status -eq 0 ]; then
		cat "$_jDeOut"
	    fi
	fi
        cat << EOF >> "$_unwedgeLog"
exit $_status

EOF
        rm -f "$_jDeIn" "$_jDeOut"
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
