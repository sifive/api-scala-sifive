#!/usr/bin/env bash

set -euvo pipefail

# This script assumes that it is running from the root of api-scala-sifive
fetch_coursier=./fetch_coursier
fetch_ivy_dependencies=./fetch_ivy_dependencies
tests_path=tests

wake --init .

# This is gross because we don't have a way of preventing Wake from
# automatically picking up .wake files that only make sense in specific contexts
# such as testing.
test_wake_files=$(find . -name '*.wake.template')
for file in $test_wake_files
do
  echo "ln -snf \"$(basename $file)\" \"${file%.*}\""
  ln -snf "$(basename $file)" "${file%.*}"
done

mkdir -p scala
mkdir -p ivycache
$fetch_coursier scala
ivy_dep_files=$(find $tests_path -maxdepth 2 -name 'ivydependencies.json')
$fetch_ivy_dependencies --scala-dir scala --cache-dir ivycache $ivy_dep_files
