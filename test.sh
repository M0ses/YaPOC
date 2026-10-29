#!/bin/bash -x

BASEDIR=$(dirname "$0")

source "$BASEDIR/base.conf"
WORKING_COPY_PATH="$HOME/git/$GIT_TEST_REPO_NAME"

# Isolate Git executions from the user's global ~/.gitconfig
export GIT_CONFIG_GLOBAL=/dev/null

function wgit {
  git -C "$WORKING_COPY_PATH" "$@"
}

function discard_commit {
  # If HEAD has a parent commit, reset to it; otherwise reset unborn branch
  if wgit rev-parse --verify HEAD~1 >/dev/null 2>&1; then
    wgit reset --hard HEAD~1
  else
    wgit update-ref -d HEAD
    wgit rm -rf . >/dev/null 2>&1 || true
  fi
  wgit clean -fdx
}

function wgit_commit {
  local msg="$1"
  # Discard flag: 1 = discard commit on push rejection, 0 = keep commit
  local discard="${2:-0}"

  wgit add . || return 1
  wgit commit -m "$msg" || return 1
  wgit push
  local push_status=$?

  if [ $push_status -ne 0 ] && [ "$discard" -eq 1 ]; then
    discard_commit
  fi

  return $push_status
}

function ok {
  if [ "$1" -ne "$2" ]; then
    echo "Not OK - $3"
    exit 1
  else
    echo "OK - $3"
  fi
}

# Re-initialize target bare repository if writable to reset commits
if [ -d "$GIT_TEST_REPO_PATH" ] && [ -w "$GIT_TEST_REPO_PATH" ]; then
  rm -rf "$GIT_TEST_REPO_PATH/refs" "$GIT_TEST_REPO_PATH/objects"
  git -C "$GIT_TEST_REPO_PATH" init --bare >/dev/null 2>&1
fi

# Recreate fresh working copy directory
rm -rf "$WORKING_COPY_PATH"
mkdir -p "$HOME/git/" || exit 1
git -c safe.directory="$GIT_TEST_REPO_PATH" clone \
  "$GIT_TEST_REPO_PATH" "$WORKING_COPY_PATH" || exit 1

# Configure identity locally inside test repository only (avoid global mutation)
wgit config user.name "Kanku User"
wgit config user.email nobody@kanku.info

# Test 1: Files inside .osc/ directory must be rejected
TC="initial commit containing the .osc file"
mkdir -p "$WORKING_COPY_PATH/.osc" || exit 1
touch "$WORKING_COPY_PATH/.osc/.keep" || exit 1
wgit_commit "$TC" 1
ok $? 1 "$TC"

# Test 2: File ending with .obsinfo must be rejected
TC="add file with .obsinfo suffix"
touch "$WORKING_COPY_PATH/package.obsinfo" || exit 1
wgit_commit "$TC" 1
ok $? 1 "$TC"

# Test 3: File listed in _allow_files_commit must be accepted
TC="add _allow_files_commit and allowed/package.obsinfo"
cat << 'EOF' > "$WORKING_COPY_PATH/_allow_files_commit"
# Exceptions from blocklist
allowed/package.obsinfo
EOF
mkdir -p "$WORKING_COPY_PATH/allowed" || exit 1
touch "$WORKING_COPY_PATH/allowed/package.obsinfo" || exit 1
wgit_commit "$TC" 0
ok $? 0 "$TC"

# Test 4: File ending with .obscpio in a subdir must be rejected
TC="add file with .obscpio suffix in a subdir"
mkdir -p "$WORKING_COPY_PATH/subdir" || exit 1
touch "$WORKING_COPY_PATH/subdir/archive.obscpio" || exit 1
wgit_commit "$TC" 1
ok $? 1 "$TC"

# Test 5: File ending in .obsinfo.bak must be accepted
TC="add file ending in .obsinfo.bak"
touch "$WORKING_COPY_PATH/package.obsinfo.bak" || exit 1
wgit_commit "$TC" 0
ok $? 0 "$TC"

# Test 6: File with obscpio prefix and .py suffix must be accepted
TC="add file with obscpio prefix"
touch "$WORKING_COPY_PATH/obscpio_generator.py" || exit 1
wgit_commit "$TC" 0
ok $? 0 "$TC"

# Test 7: File ending with .osc must be accepted
TC="add file which ends with .osc"
touch "$WORKING_COPY_PATH/test.osc" || exit 1
wgit_commit "$TC" 0
ok $? 0 "$TC"

exit 0
