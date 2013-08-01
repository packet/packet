#
# Copyright (C) 2012-2013, The Particle project authors.
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
# The GNU General Public License is contained in the file LICENSE.
#

{
  'variables': {
    'gmock_home': 'gmock',
  },
  'targets': [
    {
      'target_name': 'gmock',
      'type': '<(library)',
      'include_dirs': [
        '<(gmock_home)/include',
        '<(gmock_home)',
      ],
     'dependencies': [
        'gtest.gyp:gtest',
      ],
     'all_dependent_settings': {
        'include_dirs': [
          '<(gmock_home)/include',
        ],
        'conditions': [
          ['OS == "mac"', {
            'defines': ['GTEST_LANG_CXX11=1', 'GTEST_USE_OWN_TR1_TUPLE=1'],
          }],
        ],
      },
      'sources': [
        '<(gmock_home)/include/gmock-actions.h',
        '<(gmock_home)/include/gmock-cardinalities.h',
        '<(gmock_home)/include/gmock-generated-actions.h',
        '<(gmock_home)/include/gmock-generated-function-mockers.h',
        '<(gmock_home)/include/gmock-generated-matchers.h',
        '<(gmock_home)/include/gmock-generated-nice-strict.h',
        '<(gmock_home)/include/gmock-matchers.h',
        '<(gmock_home)/include/gmock-printers.h',
        '<(gmock_home)/include/gmock-spec-builders.h',
        '<(gmock_home)/include/gmock.h',
        '<(gmock_home)/include/internal/gmock-generated-internal-utils.h',
        '<(gmock_home)/include/internal/gmock-internal-utils.h',
        '<(gmock_home)/include/internal/gmock-port.h',
        '<(gmock_home)/src/gmock-all.cc',
        '<(gmock_home)/src/gmock-cardinalities.cc',
        '<(gmock_home)/src/gmock-internal-utils.cc',
        '<(gmock_home)/src/gmock-matchers.cc',
        '<(gmock_home)/src/gmock-spec-builders.cc',
        '<(gmock_home)/src/gmock.cc',
      ],
    },
  ]
}
