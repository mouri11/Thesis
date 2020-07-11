#!/bin/bash

timestamp() {
    date +"%s"
}

var=$1

while [ 1 ]
do
    echo $(timestamp) $var
    var=$((var+1))
    sleep 2
done