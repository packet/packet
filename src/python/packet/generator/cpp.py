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
''' The default generator for C++. '''

__author__ = 'Soheil Hassas Yeganeh <soheil@cs.toronto.edu>'

import logging
import os.path

from packet import types
from packet.generator.base import PacketGenerator
from packet.utils.types import enum

from mako.lookup import TemplateLookup


LOG = logging.getLogger('packet.generator.cpp')

__HEADER_SUFFIX = '.h'
__SOURCE_SUFFIX = '.cc'
_PACKET_BASE = '::cyrus::io::Packet'

def __get_output_file_path(pom, output_dir):
  ''' Generates the header and source file names.
      @param pom The packet object model.
      @param output_dir The output directory.
      @return A tuple of header and source file names. '''
  file_name_prefix = os.path.join(output_dir, pom.namespace)
  return (file_name_prefix + __HEADER_SUFFIX,
          file_name_prefix + __SOURCE_SUFFIX)

def _get_output_files(pom, output_dir):
  ''' Returns the output file path.
      @return a tuple of header and source paths. '''
  header_path, source_path = __get_output_file_path(pom, output_dir)
  return (open(header_path, 'w'), open(source_path, 'w'))

def _get_qualified_name(namespace, class_name):
  ''' Returns the class's qualified name. '''
  return '%s::%s' % (namespace, class_name)

TYPE_VARIANTS = enum(NONE=0, POINTER=1, REFERENCE=2, RVALUE=3)
BUILTIN_TYPES = {
  types.CHAR.name: 'char',
  types.INT_8.name: 'int8_t',
  types.INT_16.name: 'int16_t',
  types.INT_32.name: 'int32_t',
  types.INT_64.name: 'int64_t',
  types.UNSIGNED_INT_8.name: 'uint8_t',
  types.UNSIGNED_INT_16.name: 'uint16_t',
  types.UNSIGNED_INT_32.name: 'uint32_t',
  types.UNSIGNED_INT_64.name: 'uint64_t',
}


class CppGenerator(PacketGenerator):
  ''' The generator for C++. '''

  def __init__(self):
    super(CppGenerator, self).__init__()
    self.paramters = []
    self.__indent_level = 0
    self.__indent_width = 2

  def generate_packet(self, pom, output_dir, opts):  # pylint: disable=W0613
    ''' Generates code for a single packet object model. '''
    header_file, source_file = _get_output_files(pom, output_dir)
    LOG.debug('Generating C++ code for %s in %s', pom.namespace, output_dir)

    extension_folder = self._get_extension_folder(opts)
    template_path = extension_folder if extension_folder else []
    template_path += [self.__get_template_path()]

    template_lookup = TemplateLookup(directories=template_path,
                                     module_directory='/tmp/mako_modules')

    header_template = template_lookup.get_template('cpp-header.template')
    self.__writeln(header_file,
                   header_template.render(pom=pom, include_prefix='').strip(),
                   True)
    header_file.close()

    src_template = template_lookup.get_template('cpp-source.template')
    self.__writeln(source_file,
                   src_template.render(pom=pom, include_prefix='').strip(),
                   True)
    source_file.close()

  def __get_template_path(self):  # pylint: disable=R0201
    ''' Returns the template repository path. '''
    return os.path.join(os.path.dirname(__file__), 'templates', 'cpp')

  def __writeln(self, output, text='', append_with_a_newline=False):
    ''' Writes a text in the output according to the indentation level.
        @param output: The output file/stream.
        @param text: The text.
        @param append_with_a_newline: Whether to append a new line after the
                                      text. '''
    output.write(' ' * self.__indent_level * self.__indent_width)
    output.write(text + '\n')
    if append_with_a_newline:
      output.write('\n')

