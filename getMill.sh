#!/usr/bin/env bash

DIR=$1
VERSION=$2
REMOTE=https://github.com/lihaoyi/mill/releases/download/$VERSION/$VERSION
BIN=$DIR/mill-$VERSION

echo "#!/usr/bin/env sh" >> $BIN
curl -sL $REMOTE >> $BIN
chmod +x $BIN
