#!/bin/bash

set -x


_TWOSIX_OBJ_DIR=CMakeFiles/TmpShared.dir

# Determine C++ compiler

if [ -n "$(which $CXX)" ]; then
    CPP=$CXX
else
    CPP=g++
fi

CPP="/opt/android/ndk/21.3.6528147/toolchains/llvm/prebuilt/linux-x86_64/bin/clang++"

if [ "$CPP" == "g++" ] ; then
    SHARED="-shared"
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

_py_incl="/android/x86_64/include/python3.7m -I/opt/android/ndk/21.3.6528147/sysroot/usr/include/ -I/opt/android/ndk/21.3.6528147/toolchains/llvm/prebuilt/linux-x86_64/sysroot/usr/include/c++/v1/ios -I/opt/android/ndk/21.3.6528147/sources/cxx-stl/llvm-libc++/include -I/android/x86_64/include -I/opt/android/ndk/21.3.6528147/sysroot/usr/include/x86_64-linux-android/"

# -nostdlib++

_COPT="--target=x86_64-none-linux-android29 --gcc-toolchain=/opt/android/ndk/21.3.6528147/toolchains/llvm/prebuilt/linux-x86_64 --sysroot=/opt/android/ndk/21.3.6528147/toolchains/llvm/prebuilt/linux-x86_64/sysroot -g -DANDROID -fdata-sections -ffunction-sections -funwind-tables -fstack-protector-strong -no-canonical-prefixes -D_FORTIFY_SOURCE=2 -Wformat -Werror=format-security -Wall -Wconversion -Wshadow -Werror=conversion -Werror=sign-compare -O0 -fno-limit-debug-info -fPIE -std=c++17 -MD -MT"

_LDOPT="-shared --target=x86_64-none-linux-android29 --gcc-toolchain=/opt/android/ndk/21.3.6528147/toolchains/llvm/prebuilt/linux-x86_64 --sysroot=/opt/android/ndk/21.3.6528147/toolchains/llvm/prebuilt/linux-x86_64/sysroot -g -DANDROID -fdata-sections -ffunction-sections -funwind-tables -fstack-protector-strong -no-canonical-prefixes -D_FORTIFY_SOURCE=2 -Wformat -Werror=format-security   -Wall -Wconversion -Wshadow -Werror=conversion -Werror=sign-compare -O0 -fno-limit-debug-info  -Wl,--exclude-libs,libgcc.a -Wl,--exclude-libs,libgcc_real.a -Wl,--exclude-libs,libatomic.a -static-libstdc++ -Wl,--build-id -Wl,--fatal-warnings -Qunused-arguments -Wl,--gc-sections -L. -levent -L. -lpython3.7m -L. -ljsoncpp"



_make_CLICodec ()
{
  local _OBJ_LIST="$_TWOSIX_OBJ_DIR/CLICodec.cpp.o $_TWOSIX_OBJ_DIR/StringUtility.cpp.o $_TWOSIX_OBJ_DIR/popenRWE.c.o"
  #$CPP -shared -nodefaultlibs  -o CLICodec_lib.so CLICodec_wrap.o $_OBJ_LIST $* -lpython3.7m -L. -lc++_shared
  $CPP $_LDOPT  -o CLICodec_lib.so CLICodec_wrap.o $_OBJ_LIST $* 
}

swig -c++ -python -I../include -Iinclude CLICodec.i

sed -i \
    -e 's/PyInit__CLICodec/PyInit_CLICodec_lib/'                                      \
    -e 's/"_CLICodec"/"CLICodec_lib"/g' \
    CLICodec_wrap.cxx
sed -i \
    -e 's/import _CLICodec/import CLICodec_lib/'                                    \
    -e 's/_CLICodec\./CLICodec_lib./'                                                \
    CLICodec.py

#    -e 's/_CLICodec/CLICodec_lib/g' \
# -MF -MMD
#-target x86_64-none-linux-android29
_COPT="-MP  -fdata-sections -ffunction-sections -fstack-protector-strong -funwind-tables -no-canonical-prefixes  --sysroot /opt/android/ndk/21.3.6528147/toolchains/llvm/prebuilt/linux-x86_64/sysroot -g -Wno-invalid-command-line-argument -Wno-unused-command-line-argument  -D_FORTIFY_SOURCE=2 -fno-rtti -fPIC -O2 -DNDEBUG  -DANDROID  -Wformat -Werror=format-security -I."




#-nostdlib++
#$CPP -std=c++17 -fPIC $SHARED -c CLICodec_wrap.cxx -I$_py_incl -I../include/ -Iinclude -DSWIG
#$CPP -nodefaultlibs  -fPIC $SHARED -c CLICodec_wrap.cxx -I$_py_incl -I../include/ -Iinclude -DSWIG

$CPP $_COPT -I$_py_incl -I../include/ -Iinclude -DSWIG -c CLICodec_wrap.cxx 


_make_CLICodec		# make "temporary" CLICodec_lib.so referenced by IOManager_lib.so

swig -c++ -python -I../include -Iinclude IOManager.i
sed -i  \
    -e 's/_wrap_IOManager_SetProcessMsg(/_UNUSED_wrap_IOManager_SetProcessMsg(/'        \
    -e 's/_wrap_IOManager_SetSendMsg(/_UNUSED_wrap_IOManager_SetSendMsg(/'              \
    -e 's/_wrap_IOManager_Examine(/_UNUSED_wrap_IOManager_Examine(/'                    \
    -e 's/_wrap_IOManager_Send(/_UNUSED_wrap_IOManager_Send(/'                          \
    -e 's/_wrap_IOManager_Broadcast(/_UNUSED_wrap_IOManager_Broadcast(/'                \
    -e 's/_wrap_MessageWrapper_wrap(/_UNUSED_wrap_MessageWrapper_wrap(/'                \
    -e 's/_wrap_MessageWrapper_close(/_UNUSED_wrap_MessageWrapper_close(/'              \
    -e 's/PyInit__IOManager/PyInit_IOManager_lib/'                                      \
    -e 's/"_IOManager"/"IOManager_lib"/'                                                \
    IOManager_wrap.cxx
sed -i  \
    -e 's/Examine(pMsgIn, nMsgIn,/Examine(pMsgIn,/g'                                    \
    -e 's/import _IOManager/import IOManager_lib/g'                                                       \
    -e 's/_IOManager\./IOManager_lib./g'                                                       \
    IOManager.py
#$CPP -std=c++17 -fPIC $SHARED -c IOManager_wrap.cxx -I$_py_incl -I../include/ -Iinclude -DSWIG


#-isystem /opt/android/ndk/21.3.6528147/sysroot/usr/include/sys
#-isystem /opt/android/ndk/21.3.6528147/sysroot/usr/include/linux
#-isystem /opt/android/ndk/21.3.6528147/sources/cxx-stl/llvm-libc++/include
#isystem /opt/android/ndk/21.3.6528147/toolchains/llvm/prebuilt/linux-x86_64/sysroot/usr/include/c++/v1
#-isystem /opt/android/ndk/21.3.6528147/sysroot/usr/include
#-isystem /opt/android/ndk/21.3.6528147/toolchains/llvm/prebuilt/linux-x86_64/lib64/clang/9.0.8/include     
#-isystem /android/x86_64/include/boost/compatibility/cpp_c_headers 

#  -nostdlib++
#$CPP -I/android/x86_64/include/python3.7m -I/opt/android/ndk/21.3.6528147/sysroot/usr/include/ -I/opt/android/ndk/21.3.6528147/toolchains/llvm/prebuilt/linux-x86_64/sysroot/usr/include/c++/v1/ios -I/opt/android/ndk/21.3.6528147/sources/cxx-stl/llvm-libc++/include -I/android/x86_64/include  -v -nodefaultlibs -fPIC $SHARED -c IOManager_wrap.cxx -I$_py_incl -DSWIG # -DANDROID_STL=c++_static -I../include/ -Iinclude


$CPP $_COPT -I$_py_incl -DSWIG -c IOManager_wrap.cxx  # -DANDROID_STL=c++_static -I../include/ -Iinclude 

_OBJ_LIST="$_TWOSIX_OBJ_DIR/IOManager.cpp.o"
# $CPP -shared -nodefaultlibs -nostdlib++ -o IOManager_lib.so IOManager_wrap.o $_OBJ_LIST -L. libjsoncpp.so -L. CLICodec_lib.so -lpython3.7m -L. -lc++_shared -Wl,-rpath=.

$CPP $_LDOPT -o IOManager_lib.so IOManager_wrap.o $_OBJ_LIST -L. libjsoncpp.so -L. CLICodec_lib.so -Wl,-rpath,/data/data/com.twosix.race/race/artifacts/comms/PluginCOMMSSRIPixelfed/libs

_make_CLICodec -L. libjsoncpp.so -L. IOManager_lib.so -Wl,-rpath,/data/data/com.twosix.race/race/artifacts/comms/PluginCOMMSSRIPixelfed/libs # make CLICodec_lib.so that references IOManager_lib.so
