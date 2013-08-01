#!/bin/bash

rm -rf doc tools more status
find . | grep example | xargs rm -rf
find . | grep html$ | xargs rm -rf
find . | grep htm$ | xargs rm -rf
find . | grep css$ | xargs rm -rf

UNUSED_COMPONENTS=('$phoenix$', '$fusion$', '$spirit$')

for l in $(ls libs/); do
  if [[ ${UNUSED_COMPONENTS[*]} =~ "\$$l\$" ]]; then
    echo 'Removeing boost/'$l
    echo 'Removeing libs/'$l
    rm -rf "boost/$l" "libs/$l"
  else
    echo 'Keeping boost/'$l
  fi
done

REQUIRED_LIBS=('$smart_ptr$', '$filesystem$', '$system$')

for l in $(ls libs/); do
  if [[ ${REQUIRED_LIBS[*]} =~ "\$$l\$" ]]; then
    echo 'Keeping libs/'$l
  else
    echo 'Removeing libs/'$l
    rm -rf "libs/$l"
  fi
done

