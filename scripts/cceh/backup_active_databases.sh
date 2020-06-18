#!/bin/bash
#
# Backup all active Postgres databases on the VM.
#
# Usage: ./backup_active_databases.sh
#

. `dirname "$0"`/active_databases

DATE=`date -I`

for i in $ACTIVE_DATABASES
do
    FILE="/backup/saved_databases/backup_db_${i}_${DATE}.gz"
    echo "Backing up database $i to $FILE ..."
    pg_dump "$i" | gzip > "$FILE"
done
