#!/bin/bash

timestamp() {
    date +"%s"
}

while [ 1 ]
do
    printf "\033c"
    echo -ne $(timestamp)
    tail -n$1 print_out.txt
    sleep $2
done