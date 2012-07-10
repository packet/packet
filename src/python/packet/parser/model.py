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

from packet.parser.PacketLexer import PacketLexer
from packet.parser.PacketParser import PacketParser

def parse_file(path):
  ''' Returns a pythonic PacketParser.
      @param path: Path to the packet file.
      @returns POM. '''
  return parse_stream(ANTLRFileStream(path, 'UTF8'))

def parse_string(string):
  ''' Returns a pythonic PacketParser.
      @param string: The packet file content.
      @returns POM. '''
  return parse_stream(ANTLRStringStream(string))

def parse_stream(stream):
  ''' Returns a pythonic PacketParser.
      @param stream: The packet stream.
      @returns POM. '''
  lexer = PacketLexer(stream)
  tokens = CommonTokenStream(lexer)
  parser = PacketParser(tokens)
  tree = parser.file().tree
  if parser.getNumberOfSyntaxErrors() > 0:
    return None

  return PacketObjectModel(tree)

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
  def __init__(self, parsed_tree):
    ''' @param parsed_tree: The parsed model for the packet. '''
    self._tree = _PythonicWrapper(parsed_tree)
    package_dict = self.__get_package_dict(self._tree)
    self.packets = []
    self.includes = []
    self.__load_packets(self._tree, package_dict)
    self.__load_includes(self._tree)

  def __get_package_dict(self, tree):  #pylint: disable=R0201
    ''' Returns the dictionary of language name to package name.'''
    package_dict = dict()
    for package in tree.package_list:
      lang = package.values[0]
      value = package.values[1][1:-1]
      package_dict[lang] = value
    return package_dict

  def __load_packets(self, tree, package_dict):
    ''' Loads the packets from the tree. '''
    for packet in tree.packet_list:
      self.packets.append(Packet(packet, package_dict))

  def __load_includes(self, tree):
    ''' Loads the includes from the tree. '''
    for include in tree.include_list:
      self.includes.append(include.values[0])

class Packet(object):  # pylint: disable=R0903
  ''' Represent a packet. '''
  def __init__(self, packet, package_dict):
    ''' @param packet: is the parsed packet structure. '''
    self.name = packet.values[0]
    self.package_dict = package_dict

    # We cannot load the Packet here, because POM runs in the context of a
    self.parent = packet.extends.values[0] if packet.extends else None

    self.annotations = []
    for annotation in packet.annotation_list:
      self.annotations.append(Annotation(annotation))

    self.fields = []
    for field in packet.field_list:
      self.fields.append(Field(field))

class Field(object):  # pylint: disable=R0903
  ''' Represents a field. '''
  def __init__(self, field):
    ''' @param field: The parsed field. '''
    self.name = field.values[0]

    self.type = field.field_type.values[0]

    # TODO(soheil): Fix sequence here.
    self.annotations = []
    for annotation in field.annotation_list:
      self.annotations.append(Annotation(annotation))

class Annotation(object):  # pylint: disable=R0903
  ''' Represents an annotation. '''
  def __init__(self, annotation):
    ''' @param annotation: is the parsed annotation structure. '''
    self.name = annotation.values[0]
    self.params = []
    for param in annotation.annotation_param_list:
      self.params.append(AnnotationParam(self, param.values[0],
                                         param.values[1]
                                             if len(param.values) == 2
                                             else None))

class AnnotationParam(object): #pylint: disable=R0903
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

