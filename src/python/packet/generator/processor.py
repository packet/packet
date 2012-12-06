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

class LengthProcessor(ModelProcessor):
  ''' Validates packets and makes sure they have a length field, and it is not
      overriden in any derived packets. '''
  def process(self, model):
    for packet in model.packets.values():
      self._set_length(packet)

  def _set_length(self, packet):  # pylint: disable=R0201
    ''' Validates and sets length in all dervied packets. '''
    if not packet:
      return

    if packet.length_field:
      if packet.parent:
        assert packet.length_field == packet.parent.length_field, \
               'Dervied packet cannot override length field: %s' % packet.name
      return

    if not packet.length_field:
      assert packet.parent, 'Packet does not have any length field: %s' % \
                            packet.name
      self._set_length(packet.parent)
      packet.length_field = packet.parent.length_field

