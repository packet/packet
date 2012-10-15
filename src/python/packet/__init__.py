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
''' The main packet package. '''

__author__ = 'Soheil Hassas Yeganeh <soheil@cs.toronto.edu>'

from packet.utils.packaging import parse_packet_path

PACKET_PATH_ENV_VAR = 'PACKET_PATH'

packet_paths = []  # pylint: disable=C0103

def boot_packet(packet_path=None):
  ''' Boots the packet system. Must be called before any other call to the
      system.
      @param packet_path The packet path.'''
  global packet_paths  # pylint: disable=W0603
  packet_paths = parse_packet_path(packet_path)
