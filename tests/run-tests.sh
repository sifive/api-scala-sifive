#!/usr/bin/env bash

set -euvo pipefail

# This script assumes that it is running from the root of the Wit workspace.
api_scala_sifive_path=./api-scala-sifive
tests_path=$api_scala_sifive_path/tests
coursier=./scala/coursier

# Install jq if it is not already (as in environment-blockci-sifive)
if hash jq 2>/dev/null; then
  # jq already installed
  jq=$(which jq)
else
  jq_linux_url=https://github.com/stedolan/jq/releases/download/jq-1.5/jq-linux64
  jq=./jq
  curl -L -o $jq $jq_linux_url
  chmod +x $jq
fi


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


# This is gross because it duplicates the logic in the Wit Scala plugin and we
#   don't have a way of telling Wit about dependencies for testing-only packages.
# It also mixes all ivy dependencies in the same project
ivy_dep_files=$(find $tests_path -name 'ivydependencies.json')
for file in $ivy_dep_files
do
  projects=$($jq -r 'keys[]' $file)
  for proj in $projects
  do
    sv=$($jq -r ".$proj.scalaVersion" $file)
    deps=$($jq -r ".$proj.dependencies | if . == null then [] else . end | .[]" $file | tr '\n' ' ')
    $coursier fetch --cache ./ivycache --scala-version $sv $deps
  done
done


wake runAPIScalaSiFiveTests Unit
