#!/bin/bash

db="$1"
q="$2"

diff -U 0 <(psql -h ntg.cceh.uni-koeln.de -U ntg "$db" -c "$q") \
          <(psql "$db" -c "$q")
