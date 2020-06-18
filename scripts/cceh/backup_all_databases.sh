#!/bin/bash
#
# Backup all Postgres databases on the VM
#
# Usage: sudo -u postgres backup_all_databases.sh
#

DATE=`date -I`
FILE="/backup/postgres/backup_db_all_${DATE}.gz"

echo "Backing up all Postgres databases to $FILE"

pg_dumpall | gzip  > "$FILE"
