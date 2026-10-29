#!/bin/bash -x
set -e
BASEDIR=$(dirname $0)

source $BASEDIR/base.conf

rm -rf "$GIT_REPO_BASE_PATH"
mkdir -p "$GIT_REPO_BASE_PATH"

chown -R $GIT_BASE_REPO_USER:$GIT_BASE_REPO_GROUP $GIT_REPO_BASE_PATH

git config --system core.hooksPath /tmp/kanku/git-hooks
git config --system init.defaultBranch $GIT_DEFAULT_BRANCH

exit 0
