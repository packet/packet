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
    'gtest_home': 'gtest',
  },
  'targets': [
    {
      'target_name': 'gtest',
      'type': '<(library)',
      'include_dirs': [
        '<(gtest_home)/include',
        '<(gtest_home)',
      ],
      'all_dependent_settings': {
        'include_dirs': [
          '<(gtest_home)/include',
        ],
        'conditions': [
          ['OS == "mac"', {
            'defines': ['GTEST_LANG_CXX11=1', 'GTEST_USE_OWN_TR1_TUPLE=1'],
          }],
        ],
      },
      'sources': [
        '<(gtest_home)/include/gtest-death-test.h',
        '<(gtest_home)/include/gtest-message.h',
        '<(gtest_home)/include/gtest-param-test.h',
        '<(gtest_home)/include/gtest-printers.h',
        '<(gtest_home)/include/gtest-spi.h',
        '<(gtest_home)/include/gtest-test-part.h',
        '<(gtest_home)/include/gtest-typed-test.h',
        '<(gtest_home)/include/gtest.h',
        '<(gtest_home)/include/gtest_pred_impl.h',
        '<(gtest_home)/include/internal/gtest-death-test-internal.h',
        '<(gtest_home)/include/internal/gtest-filepath.h',
        '<(gtest_home)/include/internal/gtest-internal.h',
        '<(gtest_home)/include/internal/gtest-linked_ptr.h',
        '<(gtest_home)/include/internal/gtest-param-util-generated.h',
        '<(gtest_home)/include/internal/gtest-param-util.h',
        '<(gtest_home)/include/internal/gtest-port.h',
        '<(gtest_home)/include/internal/gtest-string.h',
        '<(gtest_home)/include/internal/gtest-tuple.h',
        '<(gtest_home)/include/internal/gtest-type-util.h',
        '<(gtest_home)/src/gtest-all.cc',
        '<(gtest_home)/src/gtest-death-test.cc',
        '<(gtest_home)/src/gtest-filepath.cc',
        '<(gtest_home)/src/gtest-internal-inl.h',
        '<(gtest_home)/src/gtest-port.cc',
        '<(gtest_home)/src/gtest-printers.cc',
        '<(gtest_home)/src/gtest-test-part.cc',
        '<(gtest_home)/src/gtest-typed-test.cc',
        '<(gtest_home)/src/gtest.cc',
      ],
    },
    {
      'target_name': 'gtest_main',
      'type': '<(library)',
      'dependencies': [
        'gtest',
      ],
      'sources': [
        '<(gtest_home)/src/gtest_main.cc',
      ],
    }
  ]
}
