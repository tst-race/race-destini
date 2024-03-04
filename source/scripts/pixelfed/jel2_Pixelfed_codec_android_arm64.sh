#!/system/bin/sh

# Changes for Android shell:
# Shebang to /system/bin/sh
# $TMP

echo "hello from android script" >> /data/data/com.twosix.race/race/artifacts/comms/DestiniPixelfed/tmp2.log


#if [ "$SHELL" = "/system/bin/sh" ] ; then
#    # Android
TMP="/data/data/com.twosix.race/race/artifacts/comms/DestiniPixelfed/TMP"
mkdir -p $TMP
#else
#    # Not Android
#    TMP="/tmp"
#fi

__log ()
{
    echo "$(date): $1" >> "$2"
}

_logEnc ()
{
    __log "$1" $TMP/wedge.log
}

_logDec ()
{
    __log "$1" $TMP/unwedge.log
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

echo "hello 1.1 from android script" >> /data/data/com.twosix.race/race/artifacts/comms/DestiniPixelfed/tmp2.log

_wedge=$(which wedge)
_unwedge=$(which unwedge)



if [ -z "$_wedge" ]; then
    apkpath=`pm path com.twosix.race|sed -e 's/base\.apk/lib\/arm64/'|cut -d":" -f2`
    _wedge=$apkpath/libwedge.so
    _unwedge=$apkpath/libunwedge.so
fi

echo "hello2 from android" >> /data/data/com.twosix.race/race/artifacts/comms/DestiniPixelfed/tmp2.log

echo "$_wedge" >> /data/data/com.twosix.race/race/artifacts/comms/DestiniPixelfed/tmp2.log
echo "$_unwedge" >> /data/data/com.twosix.race/race/artifacts/comms/DestiniPixelfed/tmp2.log

_checkApps

_cmd=$1; shift

# https://unix.stackexchange.com/questions/14270/get-exit-status-of-process-thats-piped-to-another

case "$_cmd" in

    encode)
        _logEnc "$0 $*"
	cat > "$TMP/$$_msgIn"
	echo "hello encode from android" >> /data/data/com.twosix.race/race/artifacts/comms/DestiniPixelfed/tmp2.log
	ls -l "$TMP/$$_msgIn" >> /data/data/com.twosix.race/race/artifacts/comms/DestiniPixelfed/tmp2.log
	echo "$_wedge -data $TMP/$$_msgIn $* $TMP/$$_steg.jpg" >> /data/data/com.twosix.race/race/artifacts/comms/DestiniPixelfed/tmp2.log 

        "$_wedge" -data "$TMP/$$_msgIn" $*  "$TMP/$$_steg.jpg" >> /data/data/com.twosix.race/race/artifacts/comms/DestiniPixelfed/tmp2.log 2>&1
	_status=$?
	echo "wedge $_status" >> /data/data/com.twosix.race/race/artifacts/comms/DestiniPixelfed/tmp2.log

	if [ $_status -eq 0 ]; then
#	    cat <<EOF > $TMP/$$_resize.php
#<?php
#\$source = imagecreatefromjpeg(\$argv[1]);
#\$destination = imagecreatetruecolor(1440, 1080);
#imagecopyresampled (\$destination, \$source, 0, 0, 0, 0, 1440, 1080, 1440, 1080); 
#imagejpeg(\$destination, \$argv[2], 80);
#?>
#EOF
#	    php $TMP/$$_resize.php $TMP/$$_steg.jpg $TMP/$$_steg2.jpg > /dev/null 2>&1
#	    jpegoptim -m75 --strip-all --all-progressive $TMP/$$_steg2.jpg > /dev/null 2>&1
	    #jpegtopnm $TMP/$$_steg2.jpg > $TMP/$$_steg2.pnm
	    #ppmtojpeg -quality 45 $TMP/$$_steg2.pnm > $TMP/$$_steg3.jpg 2>&1
#	    echo "${@:1:$#-1}" >> $TMP/foo.out  #everthing except last argument	    
#	    "$_unwedge" ${@:1:$#-1} $TMP/$$_steg2.jpg $TMP/$$_out.msg > /dev/null 2>&1
#	    diff $TMP/$$_msgIn /tmp/$$_out.msg > /dev/null 2>&1
	    
#	    if [ $? -eq 0 ]; then
	    cat $TMP/$$_steg.jpg
#	    else
#		_status=11
#	    fi
	fi

#	rm -f $TMP/$$_*

        cat << EOF >> $TMP/wedge.log
exit $_status

EOF
        ;;

    decode)
        _jDeIn="$TMP/jDeIn$$.jpg"
	_jDeOut="$TMP/jDeOut$$.msg"

        _logDec "$0 $*"

        cat > "$_jDeIn"

	# weird case on image gets downloaded before jpegoptim is performed
#	grep -q "CREATOR: gd-jpeg" "$_jDeIn"
#	_status=$? 
	
#	if [ $_status -eq 0 ]; then
#	    jpegoptim -m75 --strip-all --all-progressive "$_jDeIn" > /dev/null 2>&1
#	fi

        "$_unwedge" $* "$_jDeIn" "$_jDeOut" >> /data/data/com.twosix.race/race/artifacts/comms/DestiniPixelfed/tmp3.log  2>&1
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
        cat << EOF >> $TMP/unwedge.log
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
