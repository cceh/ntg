#!/bin/bash

q="$1"

diff -U 0 <(psql -h ntg.cceh.uni-koeln.de -U ntg ntg_ph4 -c "$q") \
          <(psql ntg_ph4 -c "$q")
