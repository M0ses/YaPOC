#!/bin/bash -x

BASEDIR=$(dirname $0)

source $BASEDIR/base.conf
WORKING_COPY_PATH=$HOME/git/$GIT_TEST_REPO_NAME

function wgit {
	git -C $WORKING_COPY_PATH "$@"
}

function wgit_commit {
  wgit add . || exit 1
  wgit commit -m "$1" || exit 1
  wgit push 
}

function ok {
  if [ $1 -ne $2 ];then
    echo "Not OK - $3"
    exit 1
  else
    echo "OK - $3"
  fi
}

git config --global user.name "Kanku User"
git config --global user.email nobody@kanku.info
git config --global --add safe.directory $GIT_TEST_REPO_PATH

mkdir $HOME/git/ || exit 1
git clone $GIT_TEST_REPO_PATH $WORKING_COPY_PATH || exit 1
mkdir $WORKING_COPY_PATH/.osc/ || exit 1

TC="initial commit containing the .osc file"
touch $WORKING_COPY_PATH/.osc/.keep || exit 1
wgit_commit "$TC" 
ok $? 1 "$TC"

touch $WORKING_COPY_PATH/.forbidden_file_name
TC="add forbidden file name"
wgit_commit "$TC"
ok $? 1 "$TC"

mkdir $WORKING_COPY_PATH/subdir
touch $WORKING_COPY_PATH/subdir/.forbidden_file_name
TC="add forbidden file name in a subdir"
wgit_commit "$TC"
ok $? 1 "$TC"

touch $WORKING_COPY_PATH/test.osc
TC="add file which ends with .osc"
wgit_commit "$TC"
ok $? 0 "$TC"

exit 0
