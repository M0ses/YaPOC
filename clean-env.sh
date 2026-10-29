#!/bin/bash -x
set -e
BASEDIR=$(dirname "$0")

source "$BASEDIR/base.conf"

# Remove test bare repository and test working copy only
rm -rf "$GIT_REPO_BASE_PATH"

exit 0
