#!/bin/bash

timestamp() {
    date +"%s"
}

while [ 1 ]
do
    echo $1 $(timestamp)
    sleep $2
done