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
    'dconv_home': 'double-conversion',
    'dconv_src_home': '<(dconv_home)/src',
  },
  'targets': [
    {
      'target_name': 'dconv',
      'type': '<(library)',
      'include_dirs': [
        '<(dconv_src_home)',
      ],
     'dependencies': [
        'gtest.gyp:gtest',
      ],
     'all_dependent_settings': {
        'include_dirs': [
          '<(dconv_src_home)',
        ],
      },
      'sources': [
        '<(dconv_src_home)/bignum.cc',
        '<(dconv_src_home)/bignum-dtoa.cc',
        '<(dconv_src_home)/bignum-dtoa.h',
        '<(dconv_src_home)/bignum.h',
        '<(dconv_src_home)/cached-powers.cc',
        '<(dconv_src_home)/cached-powers.h',
        '<(dconv_src_home)/CMakeLists.txt',
        '<(dconv_src_home)/diy-fp.cc',
        '<(dconv_src_home)/diy-fp.h',
        '<(dconv_src_home)/double-conversion.cc',
        '<(dconv_src_home)/double-conversion.h',
        '<(dconv_src_home)/fast-dtoa.cc',
        '<(dconv_src_home)/fast-dtoa.h',
        '<(dconv_src_home)/fixed-dtoa.cc',
        '<(dconv_src_home)/fixed-dtoa.h',
        '<(dconv_src_home)/ieee.h',
        '<(dconv_src_home)/strtod.cc',
        '<(dconv_src_home)/strtod.h',
        '<(dconv_src_home)/utils.h',
      ],
    },
  ]
}
