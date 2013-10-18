# Copyright (C) 2012, The Cyrus project authors.
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
  'rules': [
    {
      'rule_name': 'packet-gen-cpp',
      'extension': 'packet',
      'message': 'Generating packet for <(RULE_INPUT_NAME)',
      'outputs': [
        '<(packet_output_dir)/<(RULE_INPUT_ROOT).cc',
        '<(packet_output_dir)/<(RULE_INPUT_ROOT).h',
      ],
      'action': [
        'python',
        '<(packet_pydir)/packet/cli/packetgenerator.py',
        '-l', 'cpp',
        '-o', '<(packet_output_dir)',
        '-p', '<(RULE_INPUT_DIRNAME)',
        '-r',
        '-v',
        '<(RULE_INPUT_NAME)',
      ],
    },
  ],
 'process_outputs_as_sources': 1,
 'hard_dependency': 1,
}
