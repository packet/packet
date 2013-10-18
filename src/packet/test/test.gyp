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
  'includes': [
    '../../commons.gypi',
    '../packet-commons.gypi',
    'test.gypi',
  ],
  'variables': {
    'packet_output_dir': '<(test_packet_output_dir)',
  },
  'targets': [
    {
      'target_name': 'gen_test_packet',
      'type': 'none',
      'sources': [
        #'simple.packet',
        'including.packet',
        '<(packet_output_dir)/simple.cc',
        '<(packet_output_dir)/including.cc',
      ],
      'includes': [
        '../packetgen.gypi',
      ],
      'all_dependent_settings': {
        'include_dirs': [
          '<(packet_output_dir)/..',
        ],
      },
    },
    {
      'target_name': 'test_packet',
      'type': '<(library)',
      'dependencies': [
        'gen_test_packet',
        '<(packet_dir)/src/cpp/packet/packet.gyp:packet',
      ],
      'sources': [
        '<(packet_output_dir)/simple.cc',
        '<(packet_output_dir)/including.cc',
      ],
    },
  ],
}
