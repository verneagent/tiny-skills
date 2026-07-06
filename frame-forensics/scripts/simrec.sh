#!/bin/zsh
# Record an iOS simulator while a Maestro flow runs, then extract 30fps frames.
# Usage: simrec.sh <udid> <flow.yaml> <tag> [pre-recording-command...]
#
# Output: $TMPDIR/ff-<tag>/rec.mov + f%03d.png frames.
# The app under test must already be installed on <udid> (build/install first —
# resolve the app path via xcodebuild -showBuildSettings → BUILT_PRODUCTS_DIR,
# never a DerivedData glob).
set -e
udid=$1
flow=$2
tag=$3
[[ -n "$udid" && -n "$flow" && -n "$tag" ]] || {
  echo "usage: simrec.sh <udid> <flow.yaml> <tag>" >&2
  exit 1
}
rec=${TMPDIR:-/tmp}/ff-$tag
mkdir -p "$rec"
xcrun simctl bootstatus "$udid" -b >/dev/null
(xcrun simctl io "$udid" recordVideo --force "$rec/rec.mov" &
 echo $! > "$rec/pid")
sleep 1
maestro --udid "$udid" test "$flow" 2>&1 | tail -3 || true
kill -INT "$(cat "$rec/pid")"
sleep 2
ffmpeg -y -i "$rec/rec.mov" -vf fps=30 "$rec/f%03d.png" 2>/dev/null
echo "FRAMES: $(ls "$rec" | grep -c '\.png$') in $rec"
