#!/bin/bash

DUMPS="/home/highlander/uni/prj/ntg/CCeH/dumps"

for db in "ECM_ActsPh3" "ECM_Acts_UpdatePh3" "ECM_Acts_CBGMPh3" "ECM_Acts_Mss"
do
    echo "Creating $db ..."
    mysql -e "DROP DATABASE IF EXISTS $db"
    mysql -e "CREATE DATABASE $db"
    mysql -D "$db" < "$DUMPS/$db.dump"
done

echo "Done"
