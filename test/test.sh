#!/usr/bin/env bash

## test.sh: test segway

## $Revision$
## Copyright 2011-2012 Michael M. Hoffman <mmh1@uw.edu>

set -o nounset -o pipefail -o errexit

if [ $# != 0 ]; then
    echo usage: "$0"
    exit 2
fi

TMPDIR="$(mktemp -dp . "test-$(date +%Y%m%d).XXXXXX")"

echo >&2 "entering directory $TMPDIR"
cd "$TMPDIR"

# generate a new input master
if [ "${NEW:-}" ]; then
    input_master_arg=""
else
    input_master_arg="--input-master=../data/input.master"
fi

segway --num-labels=4 --max-train-rounds=2 \
    $input_master_arg train ../data/test.genomedata traindir
segway identify+posterior ../data/test.genomedata traindir identifydir

# diff
../compare_directory.py ../data/traindir traindir || true # keep going
../compare_directory.py ../data/identifydir identifydir || true