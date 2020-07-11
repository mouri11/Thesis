#!/bin/bash

timestamp() {
    date +"%s"
}

while [ 1 ]
do
    echo $(timestamp) $1
    sleep $2
done