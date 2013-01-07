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

builtin_types = {}  # pylint: disable=C0103

class BuiltInType(object):  # pylint: disable=R0903
  ''' Represents a builtin type. '''
  def __init__(self, name, desc=None, length_in_bytes=0):
    self.name = name
    self.desc = desc
    self.length_in_bytes = length_in_bytes
    builtin_types[name] = self

UNSIGNED_INT_8 = BuiltInType('uint8', 'unsigned byte.', 1)
INT_8 = BuiltInType('int8', 'a signed byte.', 1)
CHAR = BuiltInType('char', 'an alias for int8.', 1)
UNSIGNED_INT_16 = BuiltInType('uint16', 'unsigned of two bytes.', 2)
INT_16 = BuiltInType('int16', 'signed of two bytes.', 2)
UNSIGNED_INT_32 = BuiltInType('uint32', 'unsigned of four bytes.', 4)
INT_32 = BuiltInType('int32', 'signed of four bytes.', 4)
UNSIGNED_INT_64 = BuiltInType('uint64', 'unsigned of eight bytes.', 8)
INT_64 = BuiltInType('int64', 'signed of eight bytes.', 8)
