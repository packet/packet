#
# Copyright (c) 2014, The Packet project authors. All rights reserved.
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
''' The default generator for Go.'''

__author__ = 'Soheil Hassas Yeganeh <soheil@cs.toronto.edu>'

import logging
import os.path

from packet.generator.base import PacketGenerator
from packet.generator.base import INCLUDE_PREFIX_OPT_NAME
from packet import types

LOG = logging.getLogger('packet.generator.go')

__GO_SUFFIX = '.go'

BUILTIN_TYPES = {
  types.CHAR.name: 'int8',
  types.INT_8.name: 'int8',
  types.INT_16.name: 'int16',
  types.INT_32.name: 'int32',
  types.INT_64.name: 'int64',
  types.UNSIGNED_INT_8.name: 'uint8',
  types.UNSIGNED_INT_16.name: 'uint16',
  types.UNSIGNED_INT_32.name: 'uint32',
  types.UNSIGNED_INT_64.name: 'uint64',
}


def _get_output_file(pom, output_dir):
  ''' Returns the go output file for this packet object model. '''
  directory = os.path.join(output_dir, pom.namespace)
  if not os.path.exists(directory):
    os.makedirs(directory)

  return open(os.path.join(directory, pom.namespace + __GO_SUFFIX), 'w')

class GoGenerator(PacketGenerator):
  ''' Generates Go code for packets. '''

  def __init__(self):
    super(GoGenerator, self).__init__()

  def generate_packet(self, pom, output_dir, opts):  # pylint: disable=W0613
    ''' Generates Go code for a single packet object model. '''
    src_file = _get_output_file(pom, output_dir)

    LOG.debug('Generating Go code for %s in %s', pom.namespace, src_file.name)

    template_lookup = self._get_template_lookup(opts)

    template = template_lookup.get_template('go.template')
    src_file.write(template.render(pom=pom,
                                   include_prefix=opts.get(
                                       INCLUDE_PREFIX_OPT_NAME)).strip())
    src_file.close()

