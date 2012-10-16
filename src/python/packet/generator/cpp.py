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

from packet.generator.base import PacketGenerator

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
  header_path, source_path = __get_output_file_path(pom, output_dir)
  return (open(header_path, 'w'), open(source_path, 'w'))

def _get_qualified_name(namespace, class_name):
  return '::%s::%s' % (namespace, class_name)

class CppGenerator(PacketGenerator):
  ''' The generator for C++. '''

  def __init__(self):
    super(CppGenerator, self).__init__()
    self.paramters = []
    self.__indent_level = 0;
    self.__indent_width = 2;

  def generate_packet(self, pom, output_dir, opts):
    LOG.debug('Generating C++ code for %s in %s' % (pom.namespace, output_dir))
    header_file, source_file = _get_output_files(pom, output_dir)

    for include in pom.includes:
      LOG.debug('Adding included packet %s to %s ...' %
                (include, pom.namespace))
      LOG.error('Includes are not implemented yet.')

    self._open_namespace(pom, header_file, source_file)

    for name, packet in pom.packets.iteritems():
      LOG.debug('Visiting packet: %s' % name)
      self._generate_packet(packet, header_file, source_file)

    self._close_namespace(pom, header_file, source_file)

    header_file.close()
    source_file.close()

  def __writeln_in_file(self, output, text, append_with_a_newline=False):
    ''' Writes a text in the output according to the indentation level.
        @param output: The output file/stream.
        @param text: The text.
        @param append_with_a_newline: Whether to append a new line after the
                                      text. '''
    output.write(' ' * self.__indent_level * self.__indent_width)
    output.write(text + '\n')
    if append_with_a_newline:
      output.write('\n')

  def __indent_in(self):
    self.__indent_level += 1

  def __indent_out(self):
    self.__indent_level -= 1

  def _open_namespace(self, pom, header_file, source_file):
    self.__writeln_in_file(header_file, 'namespace %s {' % pom.namespace,
                           True)
    self.__writeln_in_file(source_file, 'namespace %s {' % pom.namespace,
                           True)

  def _close_namespace(self, pom, header_file, source_file):
    self.__writeln_in_file(header_file, '}  // namespace %s' % pom.namespace,
                           True)
    self.__writeln_in_file(source_file, '}  // namespace %s' % pom.namespace,
                           True)

  def _generate_packet(self, packet, header_file, source_file):
    self.__open_class(packet, header_file)
    self.__indent_in()

    self.__start_public_section(header_file)
    self.__generate_constructor_decls(packet, header_file)
    self.__generate_destructor_decls(packet, header_file)
    self.__generate_property_decls(packet, header_file)

    self.__start_protected_section(header_file)

    self.__start_private_section(header_file)

    self.__indent_out()
    self.__close_class(packet, header_file)

    self.__generate_constructor_defs(packet, source_file)
    self.__generate_destructor_defs(packet, source_file)
    self.__generate_property_defs(packet, source_file)

  def __open_class(self, packet, header_file):
    parent_name = _PACKET_BASE if not packet.parent else \
        _get_qualified_name(packet.parent.pom.namespace, packet.parent.name)
    self.__writeln_in_file(header_file,
                           'class %s : public %s {' % (packet.name,
                                                       parent_name))

  def __start_public_section(self, output):
    self.__indent_out()
    self.__writeln_in_file(output, ' public:')
    self.__indent_in()

  def __start_protected_section(self, output):
    self.__indent_out()
    self.__writeln_in_file(output, ' protected:')
    self.__indent_in()

  def __start_private_section(self, output):
    self.__indent_out()
    self.__writeln_in_file(output, ' private:')
    self.__indent_in()

  def __generate_constructor_decls(self, packet, output):
    pass

  def __generate_destructor_decls(self, packet, output):
    pass

  def __generate_constructor_defs(self, packet, output):
    pass

  def __generate_destructor_defs(self, packet, output):
    pass

  def __close_class(self, packet, header_file):
    self.__writeln_in_file(header_file, '};', True)

  def __generate_property_decls(self, packet, header_file):
    for field in packet.fields:
      pass

  def __generate_property_defs(self, packet, source_file):
    pass
