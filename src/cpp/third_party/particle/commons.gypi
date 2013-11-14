# Copyright (C) 2013, The Cyrus project authors.
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
    # Paths.
    'particle_dir': '.',

    # Compilation flags.
    'common_cflags': [
      '-Wno-unused-local-typedefs',
      '-Wall',
    ],
    'debug_cflags': ['-g', '-O0', '<@(common_cflags)'],
    'release_cflags': ['-g', '-O3', '-Ofast', '<@(common_cflags)'],
    'debug_cflags_cc': ['-std=c++11'],
    'release_cflags_cc': ['-std=c++11'],
  },

  'target_defaults': {
    'default_configuration': 'Debug',
    'configurations': {
      'Debug': {
        'cflags': ['<@(debug_cflags)'],
        'cflags_cc': ['<@(debug_cflags_cc)'],
        'defines': ['DEBUG_BUILD__', '_GNU_SOURCE'],
        'xcode_settings': {
          'GCC_OPTIMIZATION_LEVEL': '0',
          'OTHER_CFLAGS': ['<@(debug_cflags)', '<@(debug_cflags_cc)'],
        },
        'include_dirs': [
          '<(particle_dir)/src/cpp',
        ],
      },
      'Release': {
        'cflags': ['<@(release_cflags)'],
        'cflags_cc': ['<@(release_cflags_cc)'],
        'defines': ['_GNU_SOURCE'],
        'xcode_settings': {
          'GCC_OPTIMIZATION_LEVEL': '3',
          'OTHER_CFLAGS': ['<@(release_cflags)', '<@(release_cflags_cc)'],
        },
        'include_dirs': [
          '<(particle_dir)/src/cpp',
        ],
      },
    },
  },
}

