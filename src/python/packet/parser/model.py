#
# Copyright (c) 2012-2014, The Packet project authors. All rights reserved.
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
''' Provides the POM. '''

__author__ = 'Soheil Hassas Yeganeh <soheil@cs.toronto.edu>'

import logging

from antlr3.streams import ANTLRFileStream
from antlr3.streams import ANTLRStringStream
from antlr3.streams import CommonTokenStream
from collections import OrderedDict
import os.path

import packet
from packet.annotations import create_packet_level_annotation
from packet.annotations import create_field_level_annotation
from packet.parser.PacketLexer import PacketLexer
from packet.parser.PacketParser import PacketParser
from packet.types import builtin_types
from packet.types import BuiltInType
from packet.utils.packaging import search_for_packet


LOG = logging.getLogger('packet.parser.model')

__PARSED_PACKETS = {}

def parse_file(file_path):
  ''' Returns a pythonic PacketParser.
      @param file_path: Path to the packet file.
      @returns POM. '''
  qualified_path = search_for_packet(file_path, packet.packet_paths)
  if not qualified_path:
    return None

  if __PARSED_PACKETS.get(file_path):
    return __PARSED_PACKETS.get(file_path)

  file_name = os.path.basename(file_path)
  name, ext = os.path.splitext(file_name)  # pylint: disable=W0612
  pom = parse_stream(ANTLRFileStream(qualified_path, 'UTF8'), name)
  __PARSED_PACKETS[file_path] = pom
  return pom

def parse_string(string, namespace):
  ''' Returns a pythonic PacketParser.
      @param string: The packet file content.
      @param namespace: The namespace for the packet.
      @returns POM. '''
  return parse_stream(ANTLRStringStream(string), namespace)

def parse_stream(stream, namespace):
  ''' Returns a pythonic PacketParser.
      @param stream: The packet stream.
      @param namespace: The namespace of the packet.
      @returns POM. '''
  lexer = PacketLexer(stream)
  tokens = CommonTokenStream(lexer)
  parser = PacketParser(tokens)
  tree = parser.file().tree
  if parser.getNumberOfSyntaxErrors() > 0:
    LOG.error('Unable to parse stream')
    return None

  return PacketObjectModel(tree, namespace)

class _PythonicWrapper(object):  # pylint: disable=R0903
  ''' Pythonic wrapper. '''
  def __init__(self, obj):
    ''' @param obj: The object to wrap. '''
    self._obj = obj

  def __getattr__(self, name):
    if name == 'values':
      return self.__values()

    if name == 'text':
      return self._obj.text

    is_all_children = name == 'children'
    is_list = name.endswith('_list') or is_all_children
    if is_list:
      name = name[:-5]

    children = []
    for child in self._obj.getChildren():
      if child.text.lower() == name.lower() or is_all_children:
        wrapped_child = _PythonicWrapper(child)
        if not is_list:
          return wrapped_child
        children.append(wrapped_child)
    return children

  def __values(self):
    ''' Returns a list of text representation of children. If a child is a token
        It returns the literal. '''
    values = []
    for child in self._obj.getChildren():
      values.append(child.text)
    return values

class PacketObjectModel(object):  # pylint: disable=R0903
  ''' POM (Packet Object Model) represents a file in a hierarchical structure.
  '''
  def __init__(self, parsed_tree, namespace):
    ''' @param parsed_tree: The parsed model for the packet. '''
    self._tree = _PythonicWrapper(parsed_tree)
    self.namespace = namespace
    self.package_dict = self.__get_package_dict(self._tree)
    self.includes = OrderedDict()
    self.enums = OrderedDict()
    self.packets = OrderedDict()
    self.__load_includes(self._tree)
    self.__load_enums(self._tree)
    self.__load_packets(self._tree)

  def __get_package_dict(self, tree):  # pylint: disable=R0201
    ''' Returns the dictionary of language name to package name.'''
    package_dict = dict()
    for package in tree.package_list:
      lang = package.values[0]
      value = package.values[1][1:-1]
      package_dict[lang] = value
    return package_dict

  def __load_enums(self, tree):
    ''' Loads enums from the tree. '''
    for enum in tree.enum_list:
      enum_obj = Enum(self, enum)
      self.enums[enum_obj.name] = enum_obj
      enum_obj.load_items(enum)

  def __load_packets(self, tree):
    ''' Loads the packets from the tree. '''
    for pkt in tree.packet_list:
      pkt_obj = Packet(self, pkt)
      self.packets[pkt_obj.name] = pkt_obj

  def __load_includes(self, tree):
    ''' Loads the includes from the tree. '''
    for include in tree.include_list:
      # TODO(soheil): May be remove <...> in the grammar.
      included_pom = parse_file(include.values[0][1:-1])
      if not included_pom:
        raise Exception('Cannot find the included file: %s' % include.values[0])
      self.includes[included_pom.namespace] = included_pom

  def find_packet(self, name):
    ''' Finds a packet in the object model.
        @param name: qualified packet name. '''
    the_type = self.find_type(name)
    return the_type if isinstance(the_type, Packet) else None

  def find_enum(self, name):
    ''' Finds an enum in the object model.
        @param name: qualified enum name. '''
    the_type = self.find_type(name)
    return the_type if isinstance(the_type, Enum) else None

  def find_enum_item(self, enum_ref):
    ''' Finds the enum item value. '''
    enum_reference = [child.text for child in enum_ref.children]
    enum_name = '.'.join(enum_reference[-3:-1])
    enum = self.find_enum(enum_name)
    if not enum:
      LOG.warn('Enum not found %s' % enum_name)
      return None
    return enum.items.get(enum_reference[-1])

  def find_type(self, name):
    ''' Finds a type.
        @param name: qualified type name. '''
    if not name:
      return None

    if name.find('.') == -1:
      LOG.debug('Finding %s in %s' % (name, self.namespace))
      return self.packets.get(name) or self.enums.get(name)
    else:
      # TODO(soheil): Just one level of namespaces?
      namespace = name.split('.')[0]
      type_name = name.split('.')[-1]

      if namespace == self.namespace:
        LOG.debug('Finding %s in %s' % (name, namespace))
        return self.packets.get(type_name) or self.enums.get(type_name)

      namespace_pom = self.includes.get(namespace)
      assert namespace_pom, ('Namespace not found %s' % namespace_pom)
      return namespace_pom.find_type(type_name)

class Enum(object):  # pylint: disable=R0903
  ''' Represents an enum. '''
  def __init__(self, pom, enum):
    ''' @param pom: pkt's object model.
        @param enum: is the parsed enum structure. '''
    self.name = enum.values[0]
    self.pom = pom
    self.items = OrderedDict()

  def load_items(self, enum):
    ''' Loads enum items. Note: Do not call this method in the constructor,
        as it causes problems for self referencing enums. '''
    for item in enum.enum_item_list:
      item_obj = EnumItem(self, item)
      self.items[item_obj.name] = item_obj

def get_binary_operator(opt):  #pylint: disable=R0911
  ''' Retuns the closure for the given binary operator  '''
  def add(lhs, rhs):
    ''' add. '''
    return lhs + rhs

  def sub(lhs, rhs):
    ''' Subtract.'''
    return lhs - rhs

  def mul(lhs, rhs):
    ''' Multiply. '''
    return lhs * rhs

  def div(lhs, rhs):
    ''' Devide. '''
    return lhs / rhs

  def rshift(lhs, rhs):
    ''' Right shift. '''
    return lhs >> rhs

  def lshift(lhs, rhs):
    ''' Left shift. '''
    return lhs << rhs

  if opt == '+':
    return add
  if opt == '-':
    return sub
  if opt == '*':
    return mul
  if opt == '/':
    return div
  if opt == '<<':
    return lshift
  if opt == '>>':
    return rshift
  return None

class EnumItem(object):  # pylint: disable=R0903
  ''' Represents an enum item. '''
  def __init__(self, enum, enum_item):
    ''' @param enum: The container enum.
        @param enum_item: The parsed enum item structure. '''
    self.enum = enum
    self.name = enum_item.values[0]
    self.value = self.__evaluate_value(enum_item.children[1])

  def __evaluate_value(self, enum_item):
    ''' Evaluates a math exmpression in the num_item '''
    if not enum_item.children:
      return int(enum_item.text, 0)

    if enum_item.enum_ref_list:
      item = self.enum.pom.find_enum_item(enum_item.enum_ref_list[0])
      assert item, \
          'Enum not found in value of %s' % self.name
      return item.value


    children_values = [self.__evaluate_value(child)
                       for child in enum_item.children]

    return get_binary_operator(enum_item.text)(children_values[0],
                                               children_values[1])

# TODO(soheil): Maybe extend as Type.
class Packet(object):  # pylint: disable=R0902,R0903
  ''' Represent a packet. '''
  def __init__(self, pom, pkt):
    ''' @param pom: pkt's object model.
        @param pkt: is the parsed packet structure. '''
    self.name = pkt.values[0]
    self.pom = pom
    self.children = []
    # size_info maintains a tuple. If the first element is false, the packet has
    # a fixed length, and the second element is the length. Otherwise, the
    # second element is the size field.
    self.size_info = (True, None)
    self.big_endian = False

    # We cannot load the Packet here, because POM runs in the context of a
    parent = ''.join(pkt.extends.values) if pkt.extends else 'object'
    self.parent = pom.find_packet(parent)
    if self.parent:
      self.parent.children.append(self)

    self.annotations = {}
    for annotation in pkt.annotation_list:
      annot_obj = Annotation(annotation, self)
      self.annotations[annot_obj.name] = \
          create_packet_level_annotation(self, annot_obj)

    self.fields = []
    for field in pkt.field_list:
      self.fields.append(Field(self, field))

    for field in pkt.field_list:
      self.find_field(field.values[0]).process_annotations(
          field.annotation_list)

  def find_field(self, name):
    ''' Find the field matching the field name. '''
    for field in self.fields:
      if field.name == name:
        return field
    return None

  def get_const_size(self):
    ''' Returns the fixed size. '''
    return self.size_info[1] if self.is_const_size() else None

  def get_size_field(self):
    ''' Returns the size field if the packet has a variable length. '''
    return self.size_info[1] if not self.is_const_size() else None

  def is_const_size(self):
    ''' Returns whether the packet is fixed in size. '''
    return not self.size_info[0]

  def get_type_selector_condition(self, recursive=False):
    ''' Returns the type selector condition. '''
    conditions = []
    annot = self.annotations.get('type_selector')
    if not annot:
      return conditions

    conditions = annot.get_condition()
    if recursive and self.parent:
      conditions += self.parent.get_type_selector_condition(recursive)
    return conditions

  def get_padding_info(self):
    ''' Returns the padding information of the class. '''
    return self.annotations.get('padded')

  def is_padded(self):
    ''' Whether the packet is padded. '''
    return self.get_padding_info() != None

class Field(object):  # pylint: disable=R0903
  ''' Represents a field. '''
  def __init__(self, pkt, field):
    ''' @param field: The parsed field.
        @param pkt: The field's packet. '''
    self.name = field.values[0]
    self.packet = pkt
    self.type = self._find_type('.'.join(field.field_type.values))
    self.offset = [0, ()]
    # Stores the meta data about repreated fields (ie., arrays) in the following
    #form : (SIZE_FIELD, COUNT_FIELD, COUNT)
    self.repeated_info = None
    self.annotations = {}

  def process_annotations(self, annotation_list):
    ''' A post-processing unit that process the annotation list. '''
    # TODO(soheil): Fix sequence here.
    for annotation in annotation_list:
      annot_obj = Annotation(annotation, self.packet)
      self.annotations[annot_obj.name] = \
          create_field_level_annotation(self, annot_obj)

  def is_repeated(self):
    ''' Whether the field is a repeated field. '''
    return self.repeated_info != None

  def has_implicit_size(self):
    ''' Whether the field has implicit size (repeated with no fixed size nor
        count). '''
    return self.repeated_info and self.repeated_info.has_implicit_size()

  def is_const_size_repeated(self):
    ''' Whether the field has a fixed size. '''
    return self.repeated_info and self.repeated_info.count

  def is_dynamic_repeated(self):
    ''' Whether the field is fixed in size. '''
    return self.is_repeated() and not self.is_const_size_repeated()

  def has_const_size(self):
    ''' Whether the field has a constant pre-known size. '''
    return not self.is_dynamic_repeated() and \
        (isinstance(self.type, BuiltInType) or \
         self.type.is_const_size())

  def set_repeated_info(self, size_field=None, count_field=None, count=None):
    ''' Sets the repeat info of the field. '''
    self.repeated_info = RepeatedInfo(size_field, count_field, count)

  def get_size_field(self):
    ''' Returns the size field. '''
    return self.repeated_info.size_field if self.repeated_info else None

  def get_count_field(self):
    ''' Returns the count field. '''
    return self.repeated_info.count_field if self.repeated_info else None

  def get_repeated_count(self):
    ''' Returns the constant count of a const-size repreated field. '''
    return self.repeated_info.count if self.repeated_info else None

  def get_const_size(self):
    ''' Returns the length of the field in bytes. None if can't be found. '''
    if not self.is_repeated() and self.has_const_size():
      return self.type.get_const_size()

    if self.is_const_size_repeated():
      count = self.repeated_info.count
      return self.type.get_const_size() * count

    return None

  def _find_type(self, type_name):
    ''' Finds the type. '''
    # If it is a primitive type then return it.
    type_obj = builtin_types.get(type_name)
    if type_obj:
      return type_obj
    # Now, search for included packets.
    type_obj = self.packet.pom.find_packet(type_name)
    if not type_obj:
      raise Exception('Type not found: %s' % type_name)
    return type_obj

class RepeatedInfo(object):
  ''' Stores information about repeated fields. '''
  def __init__(self, size_field=None, count_field=None, count=None):
    self.size_field = size_field
    self.count_field = count_field
    self.count = count

  def has_implicit_size(self):
    ''' Whether the field is varilable size (repated with no size nor count).
    '''
    return self.size_field == None and self.count_field == None and \
        self.count == None


class Annotation(object):  # pylint: disable=R0903
  ''' Represents an annotation. '''
  def __init__(self, annotation, pkt):
    ''' @param annotation: is the parsed annotation structure.
        @param pkt: Annotation's packet (it can annotate a field of this packet
                    or on the packet itself).'''
    self.name = annotation.values[0]
    self.packet = pkt
    self.params = []
    for param in annotation.annotation_param_list:
      self.params.append(AnnotationParam(self, param))

class AnnotationParam(object):  # pylint: disable=R0903
  ''' Represents and annotation param. '''
  def __init__(self, annotation, param):
    self.annotation = annotation
    self.name = param.values[0]
    if len(param.values) == 1:
      self.value = None
      return

    if param.enum_ref_list:
      item = self.annotation.packet.pom.find_enum_item(param.enum_ref_list[0])
      self.value = item.value if item else None
      return

    value = param.values[1]
    if value[0].startswith('"') or value[0].startswith('\''):
      self.value = value[0][1:-1]
    elif value[0].startswith('0x'):
      self.value = int(value[0], 16)
    elif value[0].find('.') != -1:
      self.value = float(value[0])
    else:
      self.value = int(value[0])

