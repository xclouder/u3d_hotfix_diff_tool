#!/bin/bash

##############################
# settings and inicilization #
##############################

SVN_SOURCE="https://svn.example.com/trunk/"
REV_PATH="/var/www/revisions/example.com/"

TIME_SPENT=$(date +%s)
REV=$(svn info $SVN_SOURCE | grep Revision | cut -d ' ' -f 2)
PREV=0
VERBOSIVE=0

USAGE_INFO="$(basename "$0") [-r REVISION_NUM] [-i PREVIOUS_REVISION_NUM] -- make an incremental svn export

where:
  -i  previous revision (default: 0)
  -h  show this help text
  -r  revision to export (default: $REV)
  -v  verbosive mode. show fetched files

current settins:
  SVN_SOURCE: $SVN_SOURCE
  REV_PATH:   $REV_PATH
"

while getopts r:i:hv option; do
  case "$option" in
    i)  PREV=$OPTARG
        ;;
    h)  echo "$USAGE_INFO"
        exit
        ;;
    r)  REV=$OPTARG
        ;;
    v)  VERBOSIVE=1
        ;;
  esac
done

EV_PATH=$REV_PATH$REV"/"

##############################
#         functions          #
##############################

promtYesOrDie(){
  while true; do
    read -e -p "$1 (y/n): " -i "y" yn
    case $yn in
      [Yy] ) break;;
      [Nn] ) echo "spent: "$((`date +%s` - $TIME_SPENT))"s"
             echo "bye bye"
             exit
             ;;
         * ) echo "Please answer (y)es or (n)o.";;
    esac
  done
}

doIncrementalExport(){
  PREV_PATH=$REV_PATH$PREV"/"
  if [ -d $PREV_PATH ]; then
    echo "copying files from: $PREV_PATH"
    cp -f -r "$PREV_PATH." $EV_PATH
    echo "fetching added and modified files since revision $PREV..."
    for FILE_SRC in $(svn diff --summarize -r $PREV:$REV $SVN_SOURCE | awk '/[AM]/ {print $2}'); do
      FILE_PATH=$(echo $FILE_SRC | sed -e "s{$SVN_SOURCE{{");
      if [ ! -d "$EV_PATH$FILE_PATH" ]; then
        TRG_DIR="$EV_PATH$(dirname $FILE_PATH)"
        mkdir -p $TRG_DIR
        svn export -r$REV -q --force $FILE_SRC "$EV_PATH$FILE_PATH"
        if [ $VERBOSIVE -eq 1 ]; then
          echo "$EV_PATH$FILE_PATH"
        fi
      fi
    done
    echo "removing deleted files and folders since revision $PREV ..."
    for FILE_SRC in $(svn diff --summarize -r $PREV:$REV $SVN_SOURCE | awk '/D/ {print $2}'); do
      FILE_PATH=$(echo $FILE_SRC | sed -e "s{$SVN_SOURCE{{");
      rm -r "$EV_PATH$FILE_PATH"
      if [ $VERBOSIVE -eq 1 ]; then
        echo "$EV_PATH$FILE_PATH"
      fi
    done
  else
    echo "previous revision does not exist at: $PREV_PATH"
    exit;
  fi
}

##############################
#       main function        #
##############################

if [ $PREV -eq 0 ]; then
  promtYesOrDie "Do you want to do full export instead of incremental, for revision $REV of repo: [$SVN_SOURCE]"
  echo "fatching source ..."
  if [ $VERBOSIVE -eq 1 ]; then
    svn export -r$REV --force $SVN_SOURCE $EV_PATH
  else
    svn export -r$REV -q --force $SVN_SOURCE $EV_PATH
  fi
else
  promtYesOrDie "Do you want to do incremental export, for revision renge $PREV:$REV of repo: [$SVN_SOURCE]"
  doIncrementalExport
fi

echo "spent: "$((`date +%s` - $TIME_SPENT))"s"
echo [done]