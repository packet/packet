#
# Copyright (C) 2012, The Packet project authors.
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
  'targets': [
    {
      'target_name': 'packet_compile_spec',
      'type': 'none',
      'dependencies': [
        'src/python/packet/parser/parser.gyp:packet_generate_parser',
      ]
    },
    {
      'target_name': 'cpp',
      'type': 'none',
      'dependencies': [
        'src/cpp/packet/packet.gyp:packet',
      ],
    },
  ]
}

