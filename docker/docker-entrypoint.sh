#!/bin/bash
set -e

if [ "$1" = 'app-server' ]; then
    echo "***********************************************"
    echo "* Point your browser to http://localhost:5000 *"
    echo "***********************************************"
    exec python3 -m server -vvv
fi

if [ "$1" = 'cbgm' ]; then
    echo "*************************"
    echo "* Running the CBGM ...  *"
    echo "*************************"
    exec python3 -m scripts.cbgm -vvv instance/acts_ph4.conf
fi
