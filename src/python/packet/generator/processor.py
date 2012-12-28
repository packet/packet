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
''' Packet object model processors. '''

__author__ = 'Soheil Hassas Yeganeh <soheil@cs.toronto.edu>'

from abc import ABCMeta
from abc import abstractmethod

from packet.types import BuiltInType

class ModelProcessor(object):
  ''' Model processors process the packet object model and add additional data
      to it. '''
  __metaclass__ = ABCMeta

  @abstractmethod
  def process(self, model):
    ''' Process the model. '''
    pass

class OffsetProcessor(ModelProcessor):
  ''' Precompute offsets for fields in the model. '''

  def process(self, model):
    ''' Process the model. '''
    for packet in model.packets.values():
      self._process_packet(packet)

  def _calculate_offset(self, packet):  # pylint: disable=R0201
    ''' Calculates cumulative offset, used for derived classes. '''
    offset_constant = 0
    intermediate_fields = []
    if not packet:
      return (offset_constant, intermediate_fields)

    if packet.parent:
      offset_constant, intermediate_fields = self._calculate_offset(
          packet.parent)

    for field in packet.fields:
      if isinstance(field.type, BuiltInType):
        offset_constant = offset_constant + field.type.length_in_bytes
      else:
        intermediate_fields.append(field)
    return (offset_constant, intermediate_fields)

  def _process_packet(self, packet):  # pylint: disable=R0201
    ''' Adds offset to all fields in the packet file. Offset of fields is a
        tuple consisting of a constant (in bytes) and a list of intermediate
        fields. For example, an offset of (2, [x, y]) means: 2 + x.len + y.len
        bytes. '''
    offset_constant, intermediate_fields = self._calculate_offset(packet.parent)
    for field in packet.fields:
      field.offset = (offset_constant, list(intermediate_fields))
      if isinstance(field.type, BuiltInType):
        offset_constant = offset_constant + field.type.length_in_bytes
      else:
        intermediate_fields.append(field)

class SizeProcessor(ModelProcessor):
  ''' Validates packets and makes sure they have a size field, and it is not
      overriden in any derived packets. '''
  def process(self, model):
    for packet in model.packets.values():
      self._set_packet_minimum_size(packet)
      self._set_size_field_in_packet(packet)
      self._set_size_field_in_fields(packet)

  def _set_packet_minimum_size(self, packet):
    ''' Finds the minimum size of a packet. '''
    packet.min_size = self._get_packet_minimum_size(packet)

  def _get_packet_minimum_size(self, packet):
    ''' Returns the minimum size of the packet. '''
    if not packet:
      return 0

    min_size = self._get_packet_minimum_size(packet.parent)
    for field in packet.fields:
      if field.repeated:
        continue

      if isinstance(field.type, BuiltInType):
        min_size += field.type.length_in_bytes
      else:
        min_size += self._get_packet_minimum_size(field.type)

    return min_size

  def _set_size_field_in_packet(self, packet):  # pylint: disable=R0201
    ''' Validates and sets size in all dervied packets. '''
    if not packet:
      return

    if packet.size_field:
      if packet.parent:
        assert packet.size_field == packet.parent.size_field, \
               'Dervied packet cannot override size field: %s' % packet.name
      return

    if not packet.size_field:
      assert packet.parent, 'Packet does not have any size field: %s' % \
                            packet.name
      self._set_size_field_in_packet(packet.parent)
      packet.size_field = packet.parent.size_field

  def _set_size_field_in_fields(self, packet):
    ''' Sets size_field for fields. '''
    i = 0
    for field in packet.fields:
      i += 1
      self._validate_repeated_field(field, i == len(packet.fields))

  def _validate_repeated_field(self, field, is_last):  # pylint: disable=R0201
    ''' Validates repeated fields in a packet. '''
    if not field:
      return

    if field.repeated and not field.size_field:
      assert len(field.packet.children) == 0, \
          'A packet with implicitly-sized arrays cannot be overriden: %s.%s' % \
              (field.packet.name, field.name)
      assert is_last, \
          'Implicitly-sized arrays can only come as the last element of a' \
          'packet: %s.%s' % (field.packet.name, field.name)

      for other_field in field.packet.fields:
        assert other_field == field or not other_field.repeated or \
            other_field.field_size, \
            'Found two implicitly size arrarys in %s' % field.packet.name

