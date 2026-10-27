#!/bin/bash -x  
set -e
BASEDIR=$(dirname $0)

source $BASEDIR/base.conf

mkdir -p $GIT_TEST_REPO_PATH


git config --system core.hooksPath /tmp/kanku/git-hooks
git config --system init.defaultBranch $GIT_DEFAULT_BRANCH

git -C $GIT_TEST_REPO_PATH init --bare

chown -R $GIT_BASE_REPO_USER:$GIT_BASE_REPO_GROUP $GIT_REPO_BASE_PATH

exit 0
