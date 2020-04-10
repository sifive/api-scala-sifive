#!/usr/bin/env bash

set -euvo pipefail

# This script assumes that it is running from the root of api-scala-sifive
tests_path=tests

$tests_path/setup-tests.sh

wake runAPIScalaSiFiveTests Unit
