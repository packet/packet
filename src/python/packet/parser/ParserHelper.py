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
''' Provides a pythonic API for the parser generated by ANTLR. '''

__author__ = 'Soheil Hassas Yeganeh <soheil@cs.toronto.edu>'

# TODO(soheil): Impelment this.

from antlr3.streams import ANTLRFileStream
from antlr3.streams import ANTLRStringStream
from antlr3.streams import CommonTokenStream

from PacketLexer import PacketLexer
from PacketParser import PacketParser

def parse_file(path):
  ''' Returns a pythonic PacketParser.
      @param path: Path to the packet file. '''
  return parse_stream(ANTLRFileStream(path))

def parse_string(string):
  ''' Returns a pythonic PacketParser.
      @param string: The packet file content. '''
  return parse_stream(ANTLRStringStream(string))

def parse_stream(stream):
  ''' Returns a pythonic PacketParser.
      @param stream: The packet stream. '''
  lexer = PacketLexer(stream)
  tokens = CommonTokenStream(lexer)
  parser = PacketParser(tokens)
  tree = parser.file().tree

  return _PythonicWrapper(tree)

class _PythonicWrapper(object):  # pylint: disable=R0903
  ''' Pythonic wrapper. '''
  def __init__(self, obj):
    ''' @param obj: The object to wrap. '''
    self._obj = obj

  def __getattr__(self, name):
    all_children = name == 'values'
    is_list = all_children or name.endswith('_list')
    name = name[:-5]
    children = []
    for child in self._obj.getChildren():
      if all_children or child.text.lower() == name.lower():
        wrapped_child = _PythonicWrapper(child)
        if not is_list:
          return wrapped_child
        children.append(wrapped_child)
    return children
