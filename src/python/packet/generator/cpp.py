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
from packet.utils.types import enum

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
  return '::%s::%s' % (namespace, class_name)

class CppNamingStrategy(object):
  ''' Default naming strategy for C++. '''
  __DEF_TEXTS = enum(ENUM='enum class',
                     CLASS='class',
                     NAMESPACE='namespace')

  def get_class_name(self, name):  # pylint: disable=R0201
    ''' Returns the class name. '''
    return name

  def get_field_name(self, name):  # pylint: disable=R0201
    ''' Returns the field name. '''
    return name

  def get_cpptype_name(self, thetype):  # pylint: disable=R0201
    ''' Returns the cpp type. '''
    return thetype.name

  def get_enum_start(self, enum_name):
    ''' Returns the line for enum opening. '''
    return '%s %s {' % (self.__DEF_TEXTS.ENUM, enum_name)

  def __get_def_block_end(self):  # pylint: disable=C0111,W0613,R0201
    return '};'

  def get_enum_end(self, enum_name):  # pylint: disable=W0613
    ''' Returns the enum end line. '''
    return self.__get_def_block_end()

  def get_enum_element(self, enum_name, element_name):  # pylint: disable=W0613,R0201,C0301
    ''' Returns the enum element name.
        @param enum_name: Enum's name.
        @param element_name: Field's name.
    '''
    return element_name.upper() + ','

  # TODO(soheil): Remove class_name and parent_class and pass the packet
  #               instead.
  def get_class_def_start(self, class_name, parent_class):
    ''' Returns the start line of class definition. '''
    if parent_class:
      definition = '%s %s : public %s ' % (self.__DEF_TEXTS.CLASS,
                                          self.get_class_name(class_name),
                                          self.get_class_name(parent_class))
    else:
      definition = '%s %s ' % (self.__DEF_TEXTS.CLASS,
                              self.get_class_name(class_name))
    return definition + '{'

  def get_class_def_end(self, class_name):  # pylint: disable=W0613
    ''' Returns the class definition end line. '''
    return self.__get_def_block_end()

  def get_ctor_prototype(self, class_name, ctor_args):  # pylint: disable=R0201
    ''' Returns the ctor prototype. '''
    ctor_name = '%s(%s)' % (class_name, ','.join(ctor_args))
    if len(ctor_args) == 1:
      ctor_name = 'explicit ' + ctor_name

    return ctor_name

  def get_dtor_prototype(self, class_name):
    ''' Returns the dtor prototype. '''
    return '~%s()' % self.get_class_name(class_name)

  def get_ctor_decl(self, class_name, ctor_args):
    ''' Returns the constructor declaration line. '''
    return self.get_ctor_prototype(class_name, ctor_args) + ';'

  def get_ctor_def_start(self, class_name, ctor_args):
    ''' Returns the constructor decleration line. '''
    return self.get_ctor_prototype(class_name, ctor_args) + ' {'

  def get_dtor_decl(self, class_name):
    ''' Returns the destructor declaration line. '''
    return self.get_dtor_prototype(class_name) + ';'

  def get_namespace_start(self, namespace_name):
    ''' Return the namespace start line. '''
    return '%s %s {' % (self.__DEF_TEXTS.NAMESPACE, namespace_name)

  def get_namespace_end(self, namespace_name):
    ''' Return the namespace end line. '''
    return '}  // %s %s' % (self.__DEF_TEXTS.NAMESPACE, namespace_name)

  def get_getter_prototype(self, field):
    ''' Returns the prototype for property getter. '''
    return '%s get_%s()' % (self.get_cpptype_name(field.type),
                            self.get_field_name(field.name))

  def get_getter_decl(self, field):
    ''' Returns the declaration for property getter. '''
    return self.get_getter_prototype(field) + ';'

  def get_getter_def_start(self, field):
    ''' Returns the definition start for property getter. '''
    return self.get_getter_prototype(field) + ' {'

  def get_getter_def_end(self, field):  # pylint: disable=W0613
    ''' Returns the getter definition end. '''
    return self.__get_def_block_end()

_PACKET_WRITE_ARGS = ['size_t packet_size']
_PACKET_READ_ARGS = ['const IoVector& io_vector', 'size_t packet_size']

class CppGenerator(PacketGenerator):
  ''' The generator for C++. '''

  def __init__(self, naming_strategy=CppNamingStrategy()):
    super(CppGenerator, self).__init__()
    self.paramters = []
    self.__indent_level = 0
    self.__indent_width = 2
    self.__naming_strategy = naming_strategy

  def generate_packet(self, pom, output_dir, opts):
    LOG.debug('Generating C++ code for %s in %s' % (pom.namespace, output_dir))
    header_file, source_file = _get_output_files(pom, output_dir)

    for include in pom.includes:
      LOG.debug('Adding included packet %s to %s ...' %
                (include, pom.namespace))
      LOG.error('Includes are not implemented yet.')

    self.__open_namespace(pom, header_file, source_file)

    for name, packet in pom.packets.iteritems():
      if packet.pom.namespace != pom.namespace and not self._is_recursvie(opts):
        continue

      LOG.debug('Visiting packet: %s' % name)
      self.__generate_packet(packet, header_file, source_file)

    self.__close_namespace(pom, header_file, source_file)

    header_file.close()
    source_file.close()

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

  def __indent_in(self):
    ''' Increases the indent level by one. '''
    self.__indent_level += 1

  def __indent_out(self):
    ''' Decreases the indent level by one. '''
    self.__indent_level -= 1

  def __open_namespace(self, pom, header_file, source_file):
    ''' Opens namespace decleration in both header and source files. '''
    self.__writeln(header_file,
                   self.__naming_strategy.get_namespace_start(pom.namespace),
                   True)
    self.__writeln(source_file,
                   self.__naming_strategy.get_namespace_start(pom.namespace),
                   True)

  def __close_namespace(self, pom, header_file, source_file):
    ''' Closes namespace decleration in both header and source files. '''
    self.__writeln(header_file,
                   self.__naming_strategy.get_namespace_end(pom.namespace),
                   True)
    self.__writeln(source_file,
                   self.__naming_strategy.get_namespace_end(pom.namespace),
                   True)

  def __generate_packet(self, packet, header_file, source_file):
    ''' Generates the packet code both decls and defs. '''
    self.__open_class(packet, header_file)
    self.__indent_in()

    self.__start_public_section(header_file)
    self.__generate_subtypes(packet, header_file)
    self.__generate_constructor_decls(packet, header_file)
    self.__generate_destructor_decls(packet, header_file)
    self.__writeln(header_file)
    self.__generate_property_decls(packet, header_file)

    self.__start_protected_section(header_file)

    self.__start_private_section(header_file)

    self.__indent_out()
    self.__close_class(packet, header_file)

    self.__generate_constructor_defs(packet, source_file)
    self.__generate_destructor_defs(packet, source_file)
    self.__generate_property_defs(packet, source_file)

  def __open_class(self, packet, header_file):
    ''' Starts a class definition. '''
    parent_name = _PACKET_BASE if not packet.parent else \
        _get_qualified_name(packet.parent.pom.namespace, packet.parent.name)
    self.__writeln(header_file,
                   self.__naming_strategy.get_class_def_start(packet.name,
                                                              parent_name))

  def __close_class(self, packet, header_file):
    ''' Finishes the class definition. '''
    self.__writeln(header_file,
                   self.__naming_strategy.get_class_def_end(packet.name), True)

  def __start_public_section(self, output):
    ''' Starts the public section. '''
    self.__indent_out()
    self.__writeln(output, ' public:')
    self.__indent_in()

  def __start_protected_section(self, output):
    ''' Starts the protected section of a class def. '''
    self.__indent_out()
    self.__writeln(output, ' protected:')
    self.__indent_in()

  def __start_private_section(self, output):
    ''' Starts the private section of a class def. '''
    self.__indent_out()
    self.__writeln(output, ' private:')
    self.__indent_in()

  def __generate_subtypes(self, packet, output):
    ''' Genereates the SubPackets enum that stores all sub packets for the
        current packet. '''
    if not packet.children:
      return

    enum_type = 'SubPackets'
    self.__open_enum(enum_type, output)
    for child in packet.children:
      self.__writeln(output,
                     self.__naming_strategy.get_enum_element(enum_type,
                                                             child.name))
    self.__close_enum(output, enum_type)

  def __open_enum(self, enum_name, output):
    ''' Starts an enum definition. '''
    self.__writeln(output, self.__naming_strategy.get_enum_start(enum_name))
    self.__indent_in()

  def __close_enum(self, output, enum_name):
    ''' Finishes the enum definition. '''
    self.__indent_out()
    self.__writeln(output, self.__naming_strategy.get_enum_end(enum_name))

  def __generate_constructor_decls(self, packet, output):
    ''' Generates constructor declarations. '''
    self.__writeln(output,
                   self.__naming_strategy.get_ctor_decl(packet.name,
                                                        _PACKET_WRITE_ARGS))
    self.__writeln(output,
                   self.__naming_strategy.get_ctor_decl(packet.name,
                                                        _PACKET_READ_ARGS))

  def __generate_constructor_defs(self, packet, output):
    ''' Generates constructor definition. '''
    pass

  def __generate_destructor_decls(self, packet, output):
    ''' Generates destructor declaration. '''
    self.__writeln(output, self.__naming_strategy.get_dtor_decl(packet.name))

  def __generate_destructor_defs(self, packet, output):
    ''' Generates destructor definitions. '''
    pass

  def __generate_property_decls(self, packet, header_file):
    ''' Generates property declaration in the header file. '''
    for field in packet.fields:
      self.__writeln(header_file, self.__naming_strategy.get_getter_decl(field))

  def __generate_property_defs(self, packet, source_file):
    ''' Generates property definitions in the source file. '''
    pass
