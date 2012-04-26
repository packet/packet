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
from packet.utils.packaging import search_for_packet
''' Base generator. '''

__author__ = 'Soheil Hassas Yeganeh <soheil@cs.toronto.edu>'

from abc import ABCMeta
from abc import abstractmethod
import logging

from packet.parser.ParserHelper import parse_file

LOG = logging.getLogger('packet.generator.base')

class PacketGenerator(object):
  __metaclass__ = ABCMeta
  ''' All packet code generators must extend this class. '''
  def __init__(self, packet_file, packet_path):
    ''' @param packet_file: The packet file.
        @param packet_path: The path(s) to look for packets. It's a 'colon'
                            separated string. '''
    self._packet_file = packet_file
    self._packet_path = packet_path
    self._packets = {}

  def generate(self, output_dir, recursive=False):
    ''' Geneates code based for the packet file.
        Generators: Don't override this method.
        @param output_buffer: The output directory for generators.
        @param recursive: Generate code recursively for included packet files.
    '''
    self.__process_file(self._packet_file)

  def __process_file(self, packet_file):
    parsed_packet_file = parse_file(packet_file)
    self.__process_includes(parsed_packet_file.include_list)
    self.__process_packets(parsed_packet_file.packet_list)

  def __process_includes(self, includes):
    for include in includes:
      included_packet_path = include.values[0].text
      file_found = search_for_packet(included_packet_path,
                                           self._packet_path)
      if not file_found:
        LOG.warn('Packet not found: %s ' % included_packet_path)
        continue

      self.__process_file(file_found)

  def __process_packets(self, packets):
    pass

  @abstractmethod
  def generate_include(self, include):
    pass

  @abstractmethod
  def generate_packet(self, packet):
    pass
