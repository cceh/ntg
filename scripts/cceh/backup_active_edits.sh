#!/bin/bash
#
# Backup all edits on active Postgres databases
#
# Usage: ./backup_active_edits.sh
#

. `dirname "$0"`/active_databases

DATE=`date -I`

for i in $ACTIVE_DATABASES
do
    FILE="/backup/saved_edits/saved_edits_${i}_${DATE}.xml.gz"
    echo "Saving edits of $i to $FILE ..."
    python3 -m scripts.cceh.save_edits -vvv -o - "instance/$i.conf" | gzip > "$FILE"
done
