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
''' Unit tests for the packet parser. '''

__author__ = 'Soheil Hassas Yeganeh <soheil@cs.toronto.edu>'

from unittest.case import TestCase
from unittest.loader import makeSuite
from unittest.runner import TextTestRunner
from unittest.suite import TestSuite

from packet import boot_packet
from packet.parser.model import parse_file
from packettests.unit import get_packet_repo_path

# pylint: disable=C0111

_PACKET_EXT = '.packet'

SIMPLE = {
          'namespace': 'simple',
          'file': 'simple.packet',
          'packets': [{
                        'name': 'Simple',
                        'fields': [{
                                    'name': 'x',
                                    'type': 'uint8',
                                    }],
                       },
                       {
                        'name': 'SimpleParent',
                        'fields': [{
                                    'name': 'c',
                                    'type': 'char',
                                    }],
                       },
                       {
                        'name': 'AnotherSimple',
                        'parent': 'simple.SimpleParent',
                        'fields': [{
                                    'name': 'y',
                                    'type': 'Simple',
                                    }],
                       }]}

INCLUDING = {
          'namespace': 'including',
          'file': 'including.packet',
          'packets': [{
                        'name': 'Including',
                        'parent': 'simple.SimpleParent',
                        'fields': [{
                                    'name': 's',
                                    'type': 'simple.Simple',
                                    }],
                       }]}


class TestParser(TestCase):  # pylint: disable=R0904
  def __init__(self, method_name):
    TestCase.__init__(self, method_name)
    boot_packet(get_packet_repo_path())

  def _assert_packet_dict(self, packet_file_dict):
    pom = parse_file(packet_file_dict['file'])
    self.assertIsNotNone(pom, 'Cannot parse the file %s' %
                         packet_file_dict['file'])
    self.assertEqual(pom.namespace, packet_file_dict['namespace'],
                     'Name space is %s. Should be %s' %
                     (pom.namespace, packet_file_dict['namespace']))

    for packet_dict in packet_file_dict['packets']:
      self._assert_packet(pom, packet_dict['name'], packet_dict.get('parent'))
      packet = pom.find_packet(packet_dict['name'])
      for field in packet_dict['fields']:
        self._assert_field(packet, field['name'], field['type'])

  def _assert_packet(self, pom, packet_name, parent):
    packet = pom.packets.get(packet_name)
    self.assertIsNotNone(packet, 'Packet %s does not exist.' % packet_name)
    if parent and parent != 'object':
      p_ns = parent.split('.')[0]
      p_name = parent.split('.')[1]
      self.assertIsNotNone(packet.parent,
                           'Packet %s has no parent. Expected: %s' %
                           (packet_name, parent))
      self.assertEqual(packet.parent.name, p_name, 'Parent is %s. Expected %s' %
                       (packet.parent.name, p_name))
      self.assertEqual(packet.parent.pom.namespace, p_ns)

  def _assert_field(self, packet, field_name, field_type):
    field = None
    for tmp_field in packet.fields:
      if tmp_field.name == field_name:
        field = tmp_field
        break

    self.assertIsNotNone(field, 'Cannot find field %s in %s' % (field_name,
                                                                packet.name))
    type_parts = field_type.split('.')
    type_name = type_parts[-1]
    self.assertEqual(field.type.name, type_name,
                     '%s is not of type %s instead is of %s' % (field_name,
                                                                type_name,
                                                                field.type.name)
                     )
    if len(type_parts) > 1:
      type_ns = type_parts[-2]
      self.assertEqual(field.type.pom.namespace, type_ns,
                     'Namespaces does not match %s <> %s' %
                     (type_ns, field.type.pom.namespace))

  def test_simple(self):
    self._assert_packet_dict(SIMPLE)

  def test_with_include(self):
    self._assert_packet_dict(INCLUDING)

  def test_find_type(self):
    pass

def suite():
  test_suite = TestSuite()
  test_suite.addTest(makeSuite(TestParser))
  return test_suite

if __name__ == '__main__':
  TextTestRunner(verbosity=2).run(suite())
