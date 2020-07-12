#!/bin/bash

while [ 1 ]
do
    for node in $(cat standby | awk '{print $2}');do
        $(rsync ~/$(uname -n)-comp.txt ubuntu@$node:~/)
        python3 client.py -i $node -m "File sent"
    done
    sleep 2
done
