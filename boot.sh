#!/bin/bash

install_gyp() {
  pushd .
  cd third_party/gyp && sudo python setup.py install
  popd .
}

error() {
  echo "Could not generate build files."
  exit -1
}

# Install gyp if it does not exist.
hash gyp 2>&- || install_gyp

# Gyp the project.
cd build/
gyp --depth=. -Dlibrary=static_library packet.gyp

[[ $? == 0 ]] || error

echo "The build files are created in the 'build' directory."

