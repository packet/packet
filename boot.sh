#!/bin/bash

set -e

install_gyp() {
  pushd .
  cd tools/gyp && sudo python setup.py install
  popd
}

install_antlr() {
  pushd .
  cd tools/antlr/runtime/Python && sudo python setup.py install
  popd
}

not_found() {
  echo "Install $1"
  exit -1
}

build_error() {
  echo "Could not generate build files."
  exit -1
}

# Requirements.
hash python 2>&- || not_found "python & setup tools"
hash java 2>&- || not_found "java"
hash pip 2>&- || not_found "pip"

# Installations.
hash gyp 2>&- || install_gyp
# TODO(soheil): Do it via virtualenv.
sudo pip install -r requirements.txt

[[ $? == 0 ]] || build_error

echo "Run ./packet_gyp ..."

