#!/usr/bin/env bash

ROOT="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null && pwd )"
DIR=$ROOT/bin
VERSION=$1
REMOTE=https://github.com/lihaoyi/mill/releases/download/$VERSION/$VERSION
BIN=$DIR/mill-$VERSION

mkdir -p $DIR
echo "#!/usr/bin/env sh" >> $BIN
curl -sL $REMOTE >> $BIN
chmod +x $BIN
