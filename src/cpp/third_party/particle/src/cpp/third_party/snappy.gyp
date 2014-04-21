#
# Copyright (C) 2012-2014, The Particle project authors.
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
    'snappy_home': 'snappy',
  },
  'targets': [
    {
      'target_name': 'snappy',
      'type': '<(library)',
      'include_dirs': [
        '<(snappy_home)',
      ],
      'direct_dependent_settings': {
        'include_dirs': [
          '<(snappy_home)',
        ],
      },
      'sources': [
        '<(snappy_home)/linux/snappy-stubs-internal.h',
        '<(snappy_home)/snappy-internal.h',
        '<(snappy_home)/snappy-sinksource.cc',
        '<(snappy_home)/snappy-sinksource.h',
        '<(snappy_home)/snappy-stubs-internal.cc',
        '<(snappy_home)/snappy-stubs-internal.h',
        '<(snappy_home)/snappy.cc',
        '<(snappy_home)/snappy.h',
      ],
    },
    {
      'target_name': 'snappy_unittest',
      'type': 'executable',
      'defines': [
        'HAVE_SYS_MMAN_H=1',
        'HAVE_SYS_RESOURCE_H=1',
        'HAVE_SYS_TIME_H=1',
        'HAVE_GTEST=1',
      ],
      'sources': [
        '<(snappy_home)/snappy-test.cc',
        '<(snappy_home)/snappy-test.h',
        '<(snappy_home)/snappy_unittest.cc',
      ],
      'link_settings': {
        'libraries': [
          '-lpthread',
        ]
      },
      'dependencies': [
        'snappy',
        'gtest.gyp:gtest',
      ],
    },
  ],
}
