#!/bin/bash

timestamp() {
    date +"%s"
}

var=$1

file="$(uname -n)-comp.txt"
if [ -f $file ];then
    rm $file
fi

while [ 1 ]
do
    echo $(timestamp) $var >> $file
    var=$((var+1))
    sleep 2
done
