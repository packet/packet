#
# Copyright (c) 2012, The Packet project authors. All rights reserved.
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
''' Tests the packet parser. '''

__author__ = 'Soheil Hassas Yeganeh <soheil@cs.toronto.edu>'

import unittest

from packet.parser import model

_SIMPLEST_PACKET = '''
package FooLang "test";

packet Foo {
  @size(sdsd) @size(sdsd=1212) int bar;
}'''

class ParserHelperTest(unittest.TestCase):  # pylint: disable=R0904
  ''' ParserHelperTest. '''

  def test_parse_string(self):
    ''' Tests parse_string method. '''
    parsed_packet = model.parse_string(_SIMPLEST_PACKET)
    print(parsed_packet.packets[0].package_dict)
    self.assertEqual(1, len(parsed_packet.packets), 'There is only one packet.')

if __name__ == "__main__":
  #import sys;sys.argv = ['', 'Test.testName']
  unittest.main()

