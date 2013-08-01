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
    'gflags_home': 'gflags',
    'gflags_src_home': '<(gflags_home)/src',
  },
  'targets': [
    {
      'target_name': 'gflags',
      'type': '<(library)',
      'include_dirs': [
        '<(gflags_src_home)',
      ],
      'all_dependent_settings': {
        'include_dirs': [
          '<(gflags_src_home)',
        ],
      },
      'sources': [
        '<(gflags_src_home)/config.h',
        '<(gflags_src_home)/gflags/gflags_declare.h',
        '<(gflags_src_home)/gflags/gflags.h',
        '<(gflags_src_home)/gflags/gflags_completions.h',
        '<(gflags_src_home)/mutex.h',
        '<(gflags_src_home)/gflags_reporting.cc',
        '<(gflags_src_home)/linux/config.h',
        '<(gflags_src_home)/google/gflags.h',
        '<(gflags_src_home)/google/gflags_completions.h',
        '<(gflags_src_home)/gflags.cc',
        '<(gflags_src_home)/gflags_nc.cc',
        '<(gflags_src_home)/gflags_completions.cc',
        '<(gflags_src_home)/config_for_unittests.h',
        '<(gflags_src_home)/gflags_unittest.cc',
        '<(gflags_src_home)/gflags_strip_flags_test.cc',
        '<(gflags_src_home)/util.h',
      ],
    },
  ]
}
