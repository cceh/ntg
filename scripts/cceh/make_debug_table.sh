DB=ECM_Acts_BasePh3
SOURCE=05\${i}Rdg      # use like: 05\${i}Rdg
TARGET=05Rdg

i="01"
eval SRC="$SOURCE"
mysql $DB -e "CREATE OR REPLACE TABLE $TARGET LIKE $SRC"

for i in $(seq -f "%02g" 1 28)
do
    eval SRC="$SOURCE"
    CMD="INSERT INTO $TARGET SELECT * FROM $SRC"
    mysql $DB -e "$CMD"
done
