#!/bin/bash

set -e

DBNAME=`jq -r .database.name <~/backup.json`
DOCROOT=`jq -r .docroot.name <~/backup.json`
[[ -d /usr/local/backups ]] || mkdir /usr/local/backups
cd /usr/local/backups

printf -v TIMESTAMP '%(%Y-%V-%u-%m%d-%H%M%S-%s)T'
echo TIMESTAMP: $TIMESTAMP
IFS=- read YEAR WEEK DOW _ <<<$TIMESTAMP

tar cf docroot-$TIMESTAMP.tar --sort=name -C $DOCROOT .
mysqldump --add-drop-table $DBNAME >mysql-$TIMESTAMP.dump

UPLOAD=()
DELETE=()
if [[ -f docroot-$YEAR.tar ]]; then
  xdelta3 -S djw -f -s docroot-$YEAR.tar docroot-$TIMESTAMP.tar docroot-$TIMESTAMP.vcdiff
  UPLOAD+=(docroot-$TIMESTAMP.vcdiff)
  DELETE+=(docroot-$TIMESTAMP.tar)
else
  mv docroot-$TIMESTAMP.tar docroot-$YEAR.tar
  xz -9 -z -c docroot-$YEAR.tar >docroot-$YEAR.tar.xz
  UPLOAD+=(docroot-$YEAR.tar.xz)
  DELETE+=(docroot-$YEAR.tar.xz)
fi

if [[ -f mysql-$YEAR-$WEEK.dump ]]; then
  xdelta3 -S djw -f -s mysql-$YEAR-$WEEK.dump mysql-$TIMESTAMP.dump mysql-$TIMESTAMP.vcdiff
  DELETE+=(mysql-$TIMESTAMP.dump)
  UPLOAD+=(mysql-$TIMESTAMP.vcdiff)
else
  mv mysql-$TIMESTAMP.dump mysql-$YEAR-$WEEK.dump
  xz -9 -z -c mysql-$YEAR-$WEEK.dump >mysql-$YEAR-$WEEK.dump.xz
  UPLOAD+=(mysql-$YEAR-$WEEK.dump.xz)
  DELETE+=(mysql-$YEAR-$WEEK.dump.xz)
fi

python3 -u /home/ubuntu/onedrive_cli.py upload ${UPLOAD[*]}
echo upload done
rm -fv ${DELETE[*]}
