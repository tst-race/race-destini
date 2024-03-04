#!/bin/csh
mkdir ../build
cd ../build
cmake ../source
cmake --build .
cd ../source/
./pyrace.mak 
