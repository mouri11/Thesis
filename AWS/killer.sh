#!/bin/sh

if [ ! -z $1 ];then
    kill -9 $(ps aux | grep $1 | head -n1 | awk '{print $2}')
fi
