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
  'variables': {
    'packet_parser_input': 'Packet.g',
    'third_party_home': '../../../../third_party',
    'antlr_home': '<(third_party_home)/antlr',
  },
  'targets': [
    {
      'target_name': 'packet_generate_parser',
      'type': 'none',
      'dependencies': [],
      'actions': [
        {
          'action_name': 'packet_antlr',
          'inputs': [
            '<(packet_parser_input)',
          ],
          'outputs': [
            'PacketLexer.py',
            'PacketParser.py'
          ],
          'action': [
            'java',
            '-cp',
            '<(antlr_home)/antlr.jar',
            'org.antlr.Tool',
            '<(packet_parser_input)',
          ]
        },
      ]
    },
  ]
}

