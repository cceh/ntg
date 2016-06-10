#!/bin/bash

DUMPS="/home/highlander/uni/prj/ntg/CCeH/dumps"

for db in ECM_ActsPh3 ECM_Acts_BasePh3 ECM_Acts_UpdatePh3 ECM_Acts_CBGMPh3 \
                      ECM_Acts_Mss ECM_Acts_PotAncPh3 ECM_Acts_VGPh3 \
                      ECM_Acts_Sp_01Ph3 VarGenAtt_ActPh3
do
    echo "Creating $db ..."
    mysql -e "DROP DATABASE IF EXISTS $db"
    mysql -e "CREATE DATABASE $db"
    mysql -D "$db" < "$DUMPS/$db.dump"
done


echo "Done"
