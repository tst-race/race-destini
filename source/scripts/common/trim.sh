#!/bin/bash


r1=`head -c 1 /dev/urandom | od -t u1 | cut -c9-`
r2=`head -c 1 /dev/urandom | od -t u1 | cut -c9-`

echo $r1 $r2

r1=`expr $r1 % 3 + 1`
r11=`expr $r2 % 9 + 1`
r2=`expr $r2 % 8 + 1`
r21=`expr $r2 % 9 + 1`

echo $r1 $r11 $r2 $r21

ffmpeg -i $1 -ss $r1"."$r11 -t $r2"."$r21 -async 1 -an $2 > /dev/null 2>&1



