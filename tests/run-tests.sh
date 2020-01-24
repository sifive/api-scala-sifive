#!/usr/bin/env bash

set -euvo pipefail

# This script assumes that it is running from the root of the Wit workspace.

api_scala_sifive_path=./api-scala-sifive

wake --init .

# This is gross because we don't have a way of preventing Wake from
# automatically picking up .wake files that only make sense in specific contexts
# such as testing.
ln -snf "test.wake.template" "$api_scala_sifive_path/tests/test.wake"

# This is gross because we don't have a way of telling Wit about Ivy
# dependencies for testing-only packages.
./scala/coursier fetch --cache ./ivycache --scala-version 2.12.8 org.json4s::json4s-native:3.6.7

wake runAPIScalaSiFiveTests Unit
