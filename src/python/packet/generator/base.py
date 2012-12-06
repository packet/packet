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

LOG = logging.getLogger('packet.generator.base')

RECURSIVE_OPT_NAME = 'recursive'

class PacketGenerator(object):
  ''' The base class for all genrerators. All packet code generators must
      extend this class. '''
  __metaclass__ = ABCMeta
  def __init__(self):
    self._pipeline = []

  def _is_recursvie(self, opts):  # pylint: disable=R0201
    ''' Whether the option enforces recursive generation. '''
    return opts.get(RECURSIVE_OPT_NAME) == True

  def generate(self, packet_file, output_dir, opts):
    ''' Geneates code based for the packet file.
        Generators: Don't override this method.
        @param packet_file: The packet file.
        @param output_buffer: The output directory for generators.
        @param opts: Options for code generation. This class only respect the
                     'recursive' value. '''
    poms = [self._process_file(packet_file)]
    for pom in poms:
      if not pom:
        LOG.error('No such file: ' + packet_file)
        return

      LOG.info('Generating code from %s ...' % packet_file)
      self.generate_packet(pom, output_dir, opts)

      if self._is_recursvie(opts):
        for include in pom.includes.values():
          poms.append(include)

  def _process_file(self, packet_file):  # pylint: disable=R0201
    ''' Process a file, and load all packets recursively.'''
    pom = parse_file(packet_file)
    for step in self._pipeline:
      step.process(pom)
    return pom

  @abstractmethod
  def generate_packet(self, pom, output_dir, opt):
    ''' Generate code for the packet.
        @param pom: The packet object model.
        @param output_dir: The output directory for generated code.
        @param opt: options '''
    pass

