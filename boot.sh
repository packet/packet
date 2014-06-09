#!/bin/bash

set -e

install_gyp() {
  pushd .
  cd tools/gyp && sudo python setup.py install
  popd
}

error() {
  echo "Could not generate build files."
  exit -1
}

# Install gyp if it does not exist.
hash gyp 2>&- || install_gyp

[[ $? == 0 ]] || error

echo "Run ./packet_gyp ..."

