#!/bin/bash

IFS=" " read -r a b extra < <(tail -n1 $1)
echo $b