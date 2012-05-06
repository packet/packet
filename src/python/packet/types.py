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
''' Implements the packet typing system. '''

__author__ = 'Soheil Hassas Yeganeh <soheil@cs.toronto.edu>'

from abc import ABCMeta

available_types = {}  #pylint: disable=C0103

class Type(object):
  ''' The base type '''
  __metaclass__ = ABCMeta

  def __init__(self, name, desc=None, length_in_bytes=0):
    self._name = name
    self._desc = desc
    self._length_in_bytes = length_in_bytes
    available_types[name] = self

  @property
  def name(self):  #pylint: disable=C0111
    return self._name

UNSIGNED_INT_8 = Type('uint8', 'unsigned byte.', 1)
CHAR = Type('char', 'a signed byte.', 1)
UNSIGNED_INT_16 = Type('uint16', 'unsigned of two bytes.', 2)
INT_16 = Type('int16', 'signed of two bytes.', 2)
UNSIGNED_INT_32 = Type('uint32', 'unsigned of four bytes.', 4)
INT_32 = Type('int32', 'signed of four bytes.', 4)
UNSIGNED_INT_64 = Type('uint64', 'unsigned of eight bytes.', 8)
INT_64 = Type('int64', 'signed of eight bytes.', 8)
