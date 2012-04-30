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
''' Base generator. '''

__author__ = 'Soheil Hassas Yeganeh <soheil@cs.toronto.edu>'

from abc import ABCMeta
from abc import abstractmethod
import logging

from packet.parser.model import parse_file
from packet.utils.packaging import search_for_packet

LOG = logging.getLogger('packet.generator.base')

class PacketGenerator(object):
  ''' The base class for all genrerators. All packet code generators must
      extend this class. '''
  __metaclass__ = ABCMeta
  def __init__(self, packet_file, packet_path):
    ''' @param packet_file: The packet file.
        @param packet_path: The path(s) to look for packets. It's a 'colon'
                            separated string. '''
    self._packet_file = packet_file
    self._packet_path = packet_path
    self._packets = []

  @property
  def packets(self):
    ''' The list of packet and file tuples: (packet, file).'''
    return self._packets

  def find_packet(self, packet_name):
    ''' Returns a tuple of packet and file for the packet_name. '''
    for packet, packet_file in self._packets:
      if packet.name == packet_name:
        return (packet, packet_file)
    return None

  def generate(self, output_dir, recursive=False):
    ''' Geneates code based for the packet file.
        Generators: Don't override this method.
        @param output_buffer: The output directory for generators.
        @param recursive: Generate code recursively for included packet files.
    '''
    self.__process_file(self._packet_file)
    for packet, packet_file in self._packets:
      if self._packet_file != packet_file and not recursive:
        continue
      self.generate_packet(packet, output_dir)

  def __process_file(self, packet_file):
    ''' Process a file, and load all packets recursively.'''
    parsed_packet_file = parse_file(packet_file)
    self.__process_includes(parsed_packet_file.includes)
    self.__process_packets(parsed_packet_file.packets, packet_file)

  def __process_includes(self, includes):
    ''' Process an included packet. '''
    for include in includes:
      file_found = search_for_packet(include, self._packet_path)
      if not file_found:
        LOG.warn('Packet not found: %s ' % include)
        continue

      LOG.debug('Loading file: %s, included in: %s' % (file_found,
                                                       self._packet_file))
      self.__process_file(file_found)

  def __process_packets(self, packets, packet_file):
    ''' Process packets in a packet file. '''
    for packet in packets:
      LOG.debug('Packet found %s' % packet.name)
      self._packets.append((packet, packet_file))

  @abstractmethod
  def generate_packet(self, packet, output_dir):
    ''' Generate code for the packet.
        @param packet: The packet. 
        @param output_dir: The output directory for generated code. '''
    pass
