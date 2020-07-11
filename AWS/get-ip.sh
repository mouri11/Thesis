#!/bin/sh

cat active | grep $1 | awk '{print $1}'