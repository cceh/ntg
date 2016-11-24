#!/bin/bash

DUMPS="/home/highlander/uni/prj/ntg/dumps"

ulimit -n 2048 # too many open files in ECM_ActsPh4

for dump in $DUMPS/*.dump
do
    db=`basename -s .dump "$dump"`
    echo "Dropping $db ..."
    mysql -e "DROP DATABASE IF EXISTS $db"

    if [[ $dump =~ ECM_Acts_Sp_(..) ]]
    then
        if [[ "${BASH_REMATCH[1]}" > "01" ]]
        then
            continue
        fi
    fi

    echo "Creating $db ..."

    mysql -e "CREATE DATABASE $db"
    mysql -D "$db" < "$DUMPS/$db.dump"
done

echo "Done"
