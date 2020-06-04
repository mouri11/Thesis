#!/bin/bash

timestamp() {
    date +"%s"
}

val=0

while [ 1 ]
do
    val=$(ping -c1 $1 > /dev/null;echo $?)
    echo $(timestamp) $3 $val
    if [ $val -gt 0 ]
    then
        break
    fi
    sleep $2
done
