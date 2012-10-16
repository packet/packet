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
''' Command line interface for generators. '''

__author__ = 'Soheil Hassas Yeganeh <soheil@cs.toronto.edu>'

import argparse
import logging
import os
import sys

import packet
from packet import generator, boot_packet
from packet import PACKET_PATH_ENV_VAR
from packet.generator import get_generator
from packet.generator.base import RECURSIVE_OPT_NAME

LOG = logging.getLogger('packet.cli.PacketGenerator')

__PROG_NAME = "packet-gen"
__VERSION = "0.1"

def parse_args():
  ''' Parses the arguments. '''
  parser = argparse.ArgumentParser(prog=__PROG_NAME, description=
                                   'Generates code from packet files.')
  parser.add_argument('-l', '--lang', type=str, nargs=1, required=True,
                      choices=generator.supported_languages(),
                      help='generate codes in the specified language.')
  parser.add_argument('-o', '--output', type=str, nargs=1,
                      help='the output directory for generated codes.')
  parser.add_argument('-p', '--packetpath', type=str, nargs=1,
                      help='the packet path.')
  parser.add_argument('-r', '--recursive', action='store_true',
                      help='generate codes for all included packets.')
  parser.add_argument('-v', '--verbose', action='store_true',
                      help='verbose logging.')
  parser.add_argument('--version', action='version', version='%(prog)s 2.0')
  parser.add_argument('packet', type=str, nargs='+', metavar='packet-file',
                      help='The packet file(s).')

  return parser.parse_args()

def main():
  ''' Main function for packet-gen. '''
  args = parse_args()

  packet_path = args.packetpath[0]

  boot_packet(packet_path, args.verbose)

  lang = args.lang[0]

  LOG.debug('Trying to find the generator for ' + lang)
  packet_generator_class = get_generator(lang)

  if not packet_generator_class:
    LOG.error('Cannot find the generator for %s' % lang)
    sys.exit(1)

  LOG.debug('Using packet path: %s ' % str(packet.packet_paths))

  opts = {
          RECURSIVE_OPT_NAME: args.recursive
          }

  packet_generator = packet_generator_class()
  for packet_file in args.packet:
    packet_generator.generate(packet_file, args.output[0], opts)


if __name__ == '__main__':
  main()
