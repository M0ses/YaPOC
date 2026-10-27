#!/bin/bash -x  
set -e
BASEDIR=$(dirname $0)

source $BASEDIR/base.conf

rm -rf $GIT_REPO_BASE_PATH
rm -rf $HOME/git/

exit 0
