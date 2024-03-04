#!/bin/bash

#set -x

_TWOSIX_OBJ_DIR=CMakeFiles/TmpShared.dir

# Determine C++ compiler

if [ -n "$(which $CXX)" ]; then
    CPP=$CXX
else
    CPP=g++
fi

# Determine C++ Python include path

_py_vers=$(python3 --version | cut -d' ' -f 2 | sed -E -e 's/\.[0-9]+$//')
_py_incl="/usr/include/python$_py_vers"

if [ ! -d "$_py_incl" ]; then
    echo "ERROR: $_py_incl not found"
    exit 1
fi

_py_inclm="${_py_incl}m"
if [ -d "$_py_inclm" ]; then
    _py_incl="$_py_inclm"
fi

_make_CLICodec ()
{
  local _OBJ_LIST="$_TWOSIX_OBJ_DIR/CLICodec.cpp.o $_TWOSIX_OBJ_DIR/StringUtility.cpp.o $_TWOSIX_OBJ_DIR/popenRWE.c.o"
  $CPP -shared -o _CLICodec.so CLICodec_wrap.o $_OBJ_LIST -ljsoncpp -levent $*
}

swig -c++ -python -I../include -Iinclude CLICodec.i
$CPP -std=c++17 -fPIC -shared -c CLICodec_wrap.cxx -I$_py_incl -I../include/ -Iinclude -DSWIG

_make_CLICodec		# make "temporary" _CLICodec.so referenced by _IOManager.so

swig -c++ -python -I../include -Iinclude IOManager.i
sed  \
    -e 's/_wrap_IOManager_SetProcessMsg(/_UNUSED_wrap_IOManager_SetProcessMsg(/'        \
    -e 's/_wrap_IOManager_SetSendMsg(/_UNUSED_wrap_IOManager_SetSendMsg(/'              \
    -e 's/_wrap_IOManager_Examine(/_UNUSED_wrap_IOManager_Examine(/'                    \
    -e 's/_wrap_IOManager_Send(/_UNUSED_wrap_IOManager_Send(/'                          \
    -e 's/_wrap_IOManager_Broadcast(/_UNUSED_wrap_IOManager_Broadcast(/'                \
    -e 's/_wrap_MessageWrapper_wrap(/_UNUSED_wrap_MessageWrapper_wrap(/'                \
    -e 's/_wrap_MessageWrapper_close(/_UNUSED_wrap_MessageWrapper_close(/'              \
    IOManager_wrap.cxx > tempWrap

mv tempWrap IOManager_wrap.cxx

sed  \
    -e 's/Examine(pMsgIn, nMsgIn,/Examine(pMsgIn,/g'                                    \
    IOManager.py > tempManager

mv tempManager IOManager.py

$CPP -std=c++17 -fPIC -shared -c IOManager_wrap.cxx -I$_py_incl -I../include/ -Iinclude -DSWIG

_OBJ_LIST="$_TWOSIX_OBJ_DIR/IOManager.cpp.o"
$CPP -shared -o _IOManager.so IOManager_wrap.o $_OBJ_LIST -L. _CLICodec.so -Wl,-rpath=\$ORIGIN

#/usr/local/lib/race/comms/PluginCOMMSSRIPixelfed/libs -Wl,-rpath=/usr/local/lib/race/comms/PluginCOMMSSRIAvideo/libs -Wl,-rpath=/usr/local/lib/race/comms/PluginCOMMSSRIDash/libs -Wl,-rpath=/usr/local/lib/race/comms/PluginCOMMSSRIMinecraft/libs -Wl,-rpath=/usr/local/lib/race/comms/PluginCOMMSSRIImgur/libs -Wl,-rpath=/usr/local/lib/race/comms/PluginCOMMSSRITumblr/libs -Wl,-rpath=/usr/local/lib/race/comms/PluginCOMMSSRIFlickr/libs
_make_CLICodec -L. _IOManager.so -Wl,-rpath=\$ORIGIN
#/usr/local/lib/race/comms/PluginCOMMSSRIPixelfed/libs -Wl,-rpath=/usr/local/lib/race/comms/PluginCOMMSSRIAvideo/libs -Wl,-rpath=/usr/local/lib/race/comms/PluginCOMMSSRIDash/libs -Wl,-rpath=/usr/local/lib/race/comms/PluginCOMMSSRIMinecraft/libs -Wl,-rpath=/usr/local/lib/race/comms/PluginCOMMSSRIImgur/libs -Wl,-rpath=/usr/local/lib/race/comms/PluginCOMMSSRITumblr/libs -Wl,-rpath=/usr/local/lib/race/comms/PluginCOMMSSRIFlickr/libs

# make _CLICodec.so that references _IOManager.so
