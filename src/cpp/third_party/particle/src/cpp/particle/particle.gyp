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
    'particle_src_dir': '<(particle_dir)/src/cpp',
    'particle_third_party_dir': '<(particle_src_dir)/third_party',
  },
  'targets': [
    {
      'target_name': 'headers',
      'type': 'none',
      'all_dependent_settings': {
        'cflags': [
          '-pthread',
        ],
        'link_settings': {
          'libraries': [
            '-pthread',
          ],
        },
        'include_dirs': [
          '<(particle_src_dir)',
        ],
      },
      'include_dirs': [
        '<(particle_src_dir)',
      ],
      'sources': [
        'array.h',
        'bithacks.h',
        'branch.h',
        'byteordering.h',
        'functional.h',
        'memory.h',
        'ringbuffer.h',
        'thread.h',
      ],
    },
    {
      'target_name': 'signal',
      'type': '<(library)',
      'dependencies': ['headers'],
      'sources': [
        'singals.h',
        'signals.cc',
      ],
    },
    {
      'target_name': 'typename',
      'type': '<(library)',
      'dependencies': [
        '<(particle_third_party_dir)/boost.gyp:boost_common',
        'headers',
      ],
      'sources': [
        'typename.h',
        'typename.cc',
      ],
    },
    {
      'target_name': 'cpu',
      'type': '<(library)',
      'dependencies': [
        'headers',
      ],
      'sources': [
        'cpu.h',
        'cpu.cc',
      ],
    },
    {
      'target_name': 'particle_unittests',
      'type': 'executable',
      'dependencies': [
        '<@(particle_third_party_dir)/boost.gyp:boost_thread',
        '<@(particle_third_party_dir)/gtest.gyp:gtest_main',
        '<@(particle_third_party_dir)/gmock.gyp:gmock',
        'cpu',
        'headers',
        'typename',
      ],
      'sources': [
        'bithacks_test.cc',
        'boost_test.cc',
        'memory_test.cc',
        'ringbuffer_test.cc',
        'thread_test.cc',
        'typename_test.cc',
      ],
    },
  ]
}

