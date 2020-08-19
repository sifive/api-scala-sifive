#!/usr/bin/env bash

set -euvo pipefail

rm tests/.wakeignore

wake --init .
wake -x 'fetchScala Unit'
