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
from packet.types import BuiltInType
from packet.types import VariableLengthType
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

class CppTyping(object):
  ''' Provides type name generation for the C++ generator. '''
  def __init__(self):
    self.__builtin_map = {}
    self.__fill_builtin_map()

  def __fill_builtin_map(self):
    ''' Fills the built-in type map. '''
    self.__builtin_map[types.CHAR.name] = 'char'
    self.__builtin_map[types.INT_8.name] = 'int8_t'
    self.__builtin_map[types.INT_16.name] = 'int16_t'
    self.__builtin_map[types.INT_32.name] = 'int32_t'
    self.__builtin_map[types.INT_64.name] = 'int64_t'

    self.__builtin_map[types.UNSIGNED_INT_8.name] = 'uint8_t'
    self.__builtin_map[types.UNSIGNED_INT_16.name] = 'uint16_t'
    self.__builtin_map[types.UNSIGNED_INT_32.name] = 'uint32_t'
    self.__builtin_map[types.UNSIGNED_INT_64.name] = 'uint64_t'

  def get_cpp_type(self, packet_type, const=False, variant=TYPE_VARIANTS.NONE):
    ''' Returns cpp type name for any type. '''

    cpp_type = None
    builtin = isinstance(packet_type, BuiltInType)
    if builtin:
      cpp_type = self._get_builtin_type(packet_type)
    elif isinstance(packet_type, VariableLengthType):
      cpp_type = self._get_array(self.get_cpp_type(packet_type))
    else:
      cpp_type = _get_qualified_name(packet_type.pom.namespace,
                                     packet_type.name)
    if const:
      cpp_type = 'const ' + cpp_type

    # TODO(soheil): Maybe create an enum?
    if variant == TYPE_VARIANTS.POINTER:
      return '%s*' % cpp_type
    elif variant == TYPE_VARIANTS.REFERENCE:
      return '%s&' % cpp_type
    elif variant == TYPE_VARIANTS.RVALUE and not builtin:
      return '%s&&' % cpp_type
    else:
      return cpp_type

  def _get_builtin_type(self, packet_type):
    ''' Returns cpp type name for a builtin type. '''
    return self.__builtin_map.get(packet_type.name)

  def _get_array(self, element_type):  # pylint: disable=R0201
    ''' Returns a cpp array type that containts the element_type. '''
    # TODO(soheil): This is not going to work this way. We need to implement
    #               length and stuff like that.
    return 'vector<%s>' % element_type

class CppNamingStrategy(object):  # pylint: disable=R0904
  ''' Default naming strategy for C++. '''
  __DEF_TEXTS = enum(ENUM='enum class',
                     CLASS='class',
                     NAMESPACE='namespace')

  def __init__(self, typing_strategy=CppTyping()):
    self.__typing_strategy = typing_strategy

  def get_class_name(self, name):  # pylint: disable=R0201
    ''' Returns the class name. '''
    return name

  def get_field_name(self, name):  # pylint: disable=R0201
    ''' Returns the field name. '''
    return name

  def get_cpptype_name(self, thetype, const=False, variant=TYPE_VARIANTS.NONE):
    ''' Returns the C++ type. '''
    return self.__typing_strategy.get_cpp_type(thetype, const, variant)

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
    ''' Returns the constructor declaration line. '''
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

  def __get_method_prefix(self, field):
    ''' Returns method prefix for definitions. '''
    return '%s::' % self.get_class_name(field.packet.name)


  def get_getter_prototype(self, field, qualified=False):
    ''' Returns the prototype for property getter. '''
    prefix = self.__get_method_prefix(field) if qualified else ''
    return '%s %sget_%s()' % (self.get_cpptype_name(field.type),
                              prefix,
                              self.get_field_name(field.name))

  def get_setter_prototype(self, field, qualified=False):
    ''' Returns the prototype for property setter. '''
    prefix = self.__get_method_prefix(field) if qualified else ''
    return 'void {2}set_{0}({1} {0})'.format(self.get_field_name(field.name),
        self.get_cpptype_name(field.type, variant=TYPE_VARIANTS.RVALUE),
        prefix)

  def get_getter_decl(self, field):
    ''' Returns the declaration for property getter. '''
    return self.get_getter_prototype(field) + ';'

  def get_setter_decl(self, field):
    ''' Returns the declaration for property setter. '''
    return self.get_setter_prototype(field) + ';'

  def get_getter_def_start(self, field):
    ''' Returns the definition start for property getter. '''
    return self.get_getter_prototype(field, True) + ' {'

  def get_setter_def_start(self, field):
    ''' Returns the definition start for property setter. '''
    return self.get_setter_prototype(field, True) + ' {'

  def get_getter_def_end(self, field):  # pylint: disable=W0613,R0201
    ''' Returns the getter definition end. '''
    return '}'

  def get_setter_def_end(self, field):  # pylint: disable=W0613,R0201
    ''' Returns the setter definition end. '''
    return '}'

  def get_offset_method(self, field):  # pylint: disable=W0613,R0201
    ''' Returns the for the offset calculation method. '''
    return 'get_%s_offset' % field.name

  def get_offset_method_prototype(self, field):
    ''' Returns the prototype of the field's offset calculation method. '''
    return 'size_t %s()' % self.get_offset_method(field)

  def get_offset_method_decl(self, field):
    ''' Returns the declaration of the field's offset calculation method. '''
    return self.get_offset_method_prototype(field) + ';'

  def get_offset_method_def_start(self, field):
    ''' Returns definition start for field's offset calculation method. '''
    return self.get_offset_method_prototype(field) + ' {'

  def get_offset_method_def_stop(self, field):  # pylint: disable=W0613,R0201
    ''' Returns definition end for field's offset calculation method. '''
    return '}'


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

  def generate_packet(self, pom, output_dir, opts):  # pylint: disable=W0613
    ''' Generates code for a single packet object model. '''
    header_file, source_file = _get_output_files(pom, output_dir)
    LOG.debug('Generating C++ code for %s in %s' % (pom.namespace, output_dir))

    template_path = self.__get_template_path()
    template_lookup = TemplateLookup(directories=[template_path],
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

  def __get_include_str(self, include_dir,  # pylint: disable=R0201
                        include_file):
    ''' Return the include str, based on the to-be-included file and the base
        directory. '''
    return '#include "%s%s.h"' % (include_dir, include_file)

  def __generate_includes(self, pom, header_file, source_file, include_dir=''):
    ''' Generates includes in the source and header files. '''
    includes = [include.namespace for include in pom.includes.values()]
    for include in includes:
      self.__writeln(header_file, self.__get_include_str(include_dir, include))
    self.__writeln(header_file)

    self.__writeln(source_file, self.__get_include_str(include_dir,
                                                       pom.namespace), True)


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
    self.__writeln(header_file)

    self.__start_protected_section(header_file)

    self.__generate_prop_offset_decls(packet, header_file)
    self.__writeln(header_file)

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
      self.__writeln(header_file, self.__naming_strategy.get_setter_decl(field))

  def __generate_prop_offset_decls(self, packet, header_file):
    ''' Generates property declaration in the header file. '''
    for field in packet.fields:
      self.__writeln(header_file,
                     self.__naming_strategy.get_offset_method_decl(field))

  def __generate_getter_def(self, field, source_file):
    ''' Generates the getter definition for a field. '''
    self.__writeln(source_file,
                   self.__naming_strategy.get_getter_def_start(field))
    self.__indent_in()
    self.__writeln(source_file, 'auto offset = this->%s();' %
                   self.__naming_strategy.get_offset_method(field))
    if isinstance(field.type, BuiltInType):
      self.__writeln(source_file,
                     'auto value = this->get_vector().read_data<%s>(offset);' %
                     self.__naming_strategy.get_cpptype_name(field.type))
    else:
      self.__writeln(source_file,
                     'auto value = ::cyrus::packet::make_packet<%s>(' \
                     'this->get_vector(), offset);' %
                     self.__naming_strategy.get_cpptype_name(field.type))

    # TODO(soheil): add impl.
    self.__indent_out()
    self.__writeln(source_file,
                   self.__naming_strategy.get_getter_def_end(field), True)

  def __generate_setter_def(self, field, source_file):
    ''' Generates the setter definition for a field. '''
    self.__writeln(source_file,
                   self.__naming_strategy.get_setter_def_start(field))
    self.__indent_in()
    self.__indent_out()
    self.__writeln(source_file,
                   self.__naming_strategy.get_setter_def_end(field), True)

  def __generate_property_defs(self, packet, source_file):
    ''' Generates property definitions in the source file. '''
    for field in packet.fields:
      self.__generate_getter_def(field, source_file)
      self.__generate_setter_def(field, source_file)

