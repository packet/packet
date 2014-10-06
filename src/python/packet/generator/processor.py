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

import logging

from abc import ABCMeta
from abc import abstractmethod

from packet.types import BuiltInType


LOG = logging.getLogger('packet.generator.processor')


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
      if field.get_const_size():
        offset_constant += field.get_const_size()
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

      if field.get_const_size():
        offset_constant += field.get_const_size()
      else:
        intermediate_fields.append(field)


class SizeProcessor(ModelProcessor):
  ''' Validates packets and makes sure they have a size field, and it is not
      overriden in any derived packets. '''
  def process(self, model):
    for included_pom in model.includes.values():
      self.process(included_pom)

    for packet in model.packets.values():
      self._set_min_size_in_packet(packet)

    for packet in model.packets.values():
      self._set_size_info_in_packet(packet)
      self._set_size_info_in_fields(packet)

  def _set_min_size_in_packet(self, packet):
    ''' Finds the minimum size of a packet. '''
    packet.min_size = self._calculate_min_size_in_packet(packet)

  def _calculate_min_size_in_packet(self, packet):
    ''' Returns the minimum size of the packet. '''
    if not packet:
      return 0

    min_size = self._calculate_min_size_in_packet(packet.parent)
    for field in packet.fields:
      # These fields are implicitly sized.
      if not self._is_const_size(field.type) or field.is_dynamic_repeated():
        continue

      size = field.type.length_in_bytes if isinstance(field.type, BuiltInType) \
          else self._calculate_min_size_in_packet(field.type)
      count = field.get_repeated_count() if field.is_repeated() \
          else 1
      min_size += size * count

    return min_size

  def _set_size_info_in_packet(self, packet):  # pylint: disable=R0201
    ''' Validates and sets size in all dervied packets. '''
    if not packet:
      return

    self._set_size_info_in_packet(packet.parent)

    if packet.get_size_field():
      if packet.parent and packet.parent.get_size_field():
        assert packet.get_size_field() == packet.parent.get_size_field(), \
               'Dervied packet cannot override size field: %s.%s vs %s.%s' % \
               (packet.name, packet.get_size_field().name, packet.parent.name,
                packet.parent.get_size_field().name)
      return

    if self._is_const_size(packet):
      assert packet.min_size != 0, 'Packet size is zero: %s' % packet.name
      packet.size_info = (False, packet.min_size)
      return

    if not packet.parent or not packet.parent.get_size_field():
      LOG.debug('Found packet with custom size: %s', packet.name)
      packet.size_info = (True, None)
      return

    packet.size_info = (True, packet.parent.get_size_field())

  def _is_const_size(self, packet):  # pylint: disable=R0201
    ''' Wether the packet is fixed in size. '''
    if isinstance(packet, BuiltInType):
      return True

    if packet.annotations.get('custom_size'):
      return False

    if packet.get_size_field():
      return False

    if packet.parent and not self._is_const_size(packet.parent):
      return False

    for field in packet.fields:
      if field.is_dynamic_repeated() or not self._is_const_size(field.type):
        return False
    return True

  def _set_size_info_in_fields(self, packet):
    ''' Sets size_field for fields. '''
    i = 0
    for field in packet.fields:
      i += 1
      self._validate_repeated_field(field, i == len(packet.fields))

  def _validate_repeated_field(self, field, is_last):  # pylint: disable=R0201
    ''' Validates repeated fields in a packet. '''
    if not field:
      return

    if field.has_implicit_size():
      assert len(field.packet.children) == 0, \
          'A packet with implicitly-sized arrays cannot be overriden: %s.%s' % \
              (field.packet.name, field.name)
      assert is_last, \
          'Implicitly-sized arrays can only come as the last element of a' \
          'packet: %s.%s' % (field.packet.name, field.name)

      for other_field in field.packet.fields:
        assert other_field == field or not other_field.has_implicit_size(), \
            'Found two implicitly size arrarys in %s' % field.packet.name

class EndianProcessor(ModelProcessor):
  ''' Validates packets and makes sure they have a size field, and it is not
      overriden in any derived packets. '''
  def process(self, model):
    for included_pom in model.includes.values():
      self.process(included_pom)

    for packet in model.packets.values():
      self._set_endian(packet)

  def _set_endian(self, packet):
    ''' Sets the endianess of the packet. '''
    if packet.big_endian or not packet.parent:
      return

    self._set_endian(packet.parent)
    packet.big_endian = packet.parent.big_endian

