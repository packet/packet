#
# Copyright (C) 2013, The Packet project authors.
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
    'particle_cpp_src_dir': '<(particle_dir)/src/cpp',
  },
  'targets': [
    {
      'target_name': 'particle',
      'type': 'none',
      'all_dependent_settings': {
        'include_dirs': [
          '<(particle_cpp_src_dir)',
        ],
      },
      'dependencies': [
        '<(particle_cpp_src_dir)/third_party/boost.gyp:boost_common',
        '<(particle_cpp_src_dir)/third_party/folly.gyp:folly',
        '<(particle_cpp_src_dir)/third_party/glog.gyp:glog',
        '<(particle_cpp_src_dir)/third_party/sparsehash.gyp:sparsehash',
        '<(particle_cpp_src_dir)/particle/particle.gyp:headers',
        '<(particle_cpp_src_dir)/particle/particle.gyp:signal',
        '<(particle_cpp_src_dir)/particle/particle.gyp:typename',
      ],
      'sources': [
        'commons.gypi',
      ],
    },
    {
      'target_name': 'particle_testlib',
      'type': '<(library)',
      'dependencies': [
        '<(particle_cpp_src_dir)/third_party/gmock.gyp:gmock',
        '<(particle_cpp_src_dir)/third_party/gtest.gyp:gtest',
      ],
    },
    {
      'target_name': 'particle_testrunner',
      'type': 'static_library',
      'dependencies': [
        '<(particle_cpp_src_dir)/third_party/gtest.gyp:gtest_main',
      ],
    },
    {
      'target_name': 'particle_tests',
      'type': 'none',
      'dependencies': [
        '<(particle_cpp_src_dir)/particle/particle.gyp:particle_unittests',
      ],
    },
  ]
}

