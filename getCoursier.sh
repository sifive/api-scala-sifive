#!/usr/bin/env bash

DIR=$1
VERSION=$2
REMOTE=https://github.com/coursier/coursier/releases/download/v$VERSION/coursier
BIN=$DIR/coursier-$VERSION

curl -Lo $BIN $REMOTE
chmod +x $BIN
