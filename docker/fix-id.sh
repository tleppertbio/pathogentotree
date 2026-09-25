#!/bin/bash
# Make sure you are in the correct directory
cd /
directory="the_data"
if [ -d "$directory" ]; then
  cd the_data
  #dir list, get head dir '.', sed multiple space to one, cut fields 3,4 for userid and groupid
  localUID=$(ls -nla . | grep ' \.$' | sed -e's/  */ /g' | cut -d" " -f 3)
  localGRPID=$(ls -nla . | grep ' \.$' | sed -e's/  */ /g' | cut -d" " -f 4)
  chown -R $localUID:$localGRPID ./
fi
