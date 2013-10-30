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

  def get_cpp_type(self, packet_type, const=False, variant=TYPE_VARIANTS.NONE,
                   repeated_info=None):  # pylint: disable=W0613
    ''' Returns cpp type name for any type. '''

    cpp_type = None
    builtin = isinstance(packet_type, BuiltInType)
    if builtin:
      cpp_type = self._get_builtin_type(packet_type)
    else:
      cpp_type = _get_qualified_name(packet_type.pom.namespace,
                                     packet_type.name)
    if const:
      cpp_type = 'const ' + cpp_type

    if repeated_info:
      if repeated_info.count:
        cpp_type = 'std::array<%s, %d>' % (cpp_type, repeated_info.count)
      else:
        cpp_type = 'std::vector<std::shared_ptr<%s>>' % cpp_type

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

  def get_cpptype_name(self, thetype, const=False, variant=TYPE_VARIANTS.NONE,
                       repeated_info=(False, 1)):
    ''' Returns the C++ type. '''
    return self.__typing_strategy.get_cpp_type(thetype, const, variant,
                                               repeated_info)


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

