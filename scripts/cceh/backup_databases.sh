#!/bin/bash

. `dirname "$0"`/active_databases

DATE=`date -I`

for i in $ACTIVE_DATABASES
do
    echo "Backing up $i ..."
    pg_dump "$i" | gzip > "backup_db_${i}_${DATE}.gz"
done
