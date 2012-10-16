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
''' Provides the POM. '''

__author__ = 'Soheil Hassas Yeganeh <soheil@cs.toronto.edu>'

from antlr3.streams import ANTLRFileStream
from antlr3.streams import ANTLRStringStream
from antlr3.streams import CommonTokenStream
from collections import OrderedDict
import os.path

import packet
from packet.parser.PacketLexer import PacketLexer
from packet.parser.PacketParser import PacketParser
from packet.types import available_types
from packet.utils.packaging import search_for_packet


def parse_file(file_path):
  ''' Returns a pythonic PacketParser.
      @param file_path: Path to the packet file.
      @returns POM. '''
  qualified_path = search_for_packet(file_path, packet.packet_paths)
  if not qualified_path:
    return None

  file_name = os.path.basename(file_path)
  name, ext = os.path.splitext(file_name)  # pylint: disable=W0612
  return parse_stream(ANTLRFileStream(qualified_path, 'UTF8'), name)

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

    is_list = name.endswith('_list')
    if is_list:
      name = name[:-5]

    children = []
    for child in self._obj.getChildren():
      if child.text.lower() == name.lower():
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
    self.packets = OrderedDict()
    self.__load_includes(self._tree)
    self.__load_packets(self._tree)

  def __get_package_dict(self, tree):  # pylint: disable=R0201
    ''' Returns the dictionary of language name to package name.'''
    package_dict = dict()
    for package in tree.package_list:
      lang = package.values[0]
      value = package.values[1][1:-1]
      package_dict[lang] = value
    return package_dict

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
    ''' finds a packet.
        @param name: qualified packet name. '''
    if not name:
      return None

    if name.find('.') == -1:
      return self.packets.get(name)
    else:
      # TODO(soheil): Just one level of namespaces?
      namespace = name.split('.')[0]
      pkt = name.split('.')[-1]
      if namespace == self.namespace:
        return self.packets.get(pkt)

      namespace_pom = self.includes.get(namespace)
      return namespace_pom.find_packet(pkt) if namespace_pom else None

# TODO(soheil): Maybe extend as Type.
class Packet(object):  # pylint: disable=R0903
  ''' Represent a packet. '''
  def __init__(self, pom, pkt):
    ''' @param pom: pkt's object model.
        @param pkt: is the parsed packet structure.
        '''
    self.name = pkt.values[0]
    self.pom = pom
    self.children = []

    # We cannot load the Packet here, because POM runs in the context of a
    parent = ''.join(pkt.extends.values) if pkt.extends else 'object'
    self.parent = pom.find_packet(parent)
    if self.parent:
      self.parent.children.append(self)

    self.annotations = []
    for annotation in pkt.annotation_list:
      self.annotations.append(Annotation(self, annotation))

    self.fields = []
    for field in pkt.field_list:
      self.fields.append(Field(self, field))

class Field(object):  # pylint: disable=R0903
  ''' Represents a field. '''
  def __init__(self, pkt, field):
    ''' @param field: The parsed field.
        @param pkt: The field's packet. '''
    self.name = field.values[0]

    self.packet = pkt
    self.type = self._find_type('.'.join(field.field_type.values))

    # TODO(soheil): Fix sequence here.
    self.annotations = []
    for annotation in field.annotation_list:
      self.annotations.append(Annotation(annotation))

  def _find_type(self, type_name):
    ''' Finds the type. '''
    # If it is a primitive type then return it.
    type_obj = available_types.get(type_name)
    if type_obj:
      return type_obj
    # Now, search for included packets.
    type_obj = self.packet.pom.find_packet(type_name)
    if not type_obj:
      raise Exception('Type not found: %s' % type_name)
    return type_obj

class Annotation(object):  # pylint: disable=R0903
  ''' Represents an annotation. '''
  def __init__(self, pkt, annotation):
    ''' @param annotation: is the parsed annotation structure.
        @param pkt: annotation's packet. '''
    self.name = annotation.values[0]
    self.packet = pkt
    self.params = []
    for param in annotation.annotation_param_list:
      self.params.append(AnnotationParam(self, param.values[0],
                                         param.values[1]
                                             if len(param.values) == 2
                                             else None))

class AnnotationParam(object):  # pylint: disable=R0903
  ''' Represents and annotation param. '''
  def __init__(self, annotation, name, value):
    self.annotation = annotation
    self.name = name
    if value == None:
      self.value = None
    elif value.startswith('"') or value.startswith('\''):
      self.value = value[1:-1]
    elif value.startswith('0x'):
      self.value = int(value, 16)
    elif value.find('.') != -1:
      self.value = float(value)
    else:
      self.value = int(value)

