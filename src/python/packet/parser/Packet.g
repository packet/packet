/*
 * Copyright (c) 2012, The Packet project authors. All rights reserved.
 *
 * This program is free software: you can redistribute it and/or modify
 * it under the terms of the GNU General Public License as published by
 * the Free Software Foundation, either version 3 of the License, or
 * (at your option) any later version.
 *
 * This program is distributed in the hope that it will be useful,
 * but WITHOUT ANY WARRANTY; without even the implied warranty of
 * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
 * GNU General Public License for more details
 *
 * You should have received a copy of the GNU General Public License
 * along with this program.  If not, see <http://www.gnu.org/licenses/>.
 *
 * The GNU General Public License is contained in the file LICENSE.
 */
grammar Packet;

options {
  language = Python;
  output = AST;
}

@header {
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

import sys
import traceback

from PacketLexer import PacketLexer

}

@main {
def main(argv, otherArg=None):
  char_stream = ANTLRFileStream(sys.argv[1])
  lexer = PacketLexer(char_stream)
  tokens = CommonTokenStream(lexer)
  parser = PacketParser(tokens);

  try:
    parser.expr()
  except RecognitionException:
    traceback.print_stack()
}

/*
 * Parser rules.
 */
file:
	expr+;

expr:
  include
  | packet;

include:
  'import' path SEMICOLON;

packet:
  packet_def LBRAC packet_body RBRAC
  ;

packet_def:
  annotations 'packet' packet_name ( LPRAN parent_packet_name RPRAN )?
  ;

parent_packet_name:
  packet_name
  | 'object';

packet_body:
   (field SEMICOLON)*
   ;

field:
  sequence? annotations  field_type field_name
  ;

sequence:
  ( NUMBER ) COLON
  ;

annotations:
  ( annotation )*
  ;

annotation:
  AT IDENTIFIER annotation_param*
  ;

annotation_param:
  LPRAN IDENTIFIER ( COMMA IDENTIFIER )* RPRAN
  ;

packet_name: IDENTIFIER;

field_name: IDENTIFIER;

field_type: IDENTIFIER;

name: IDENTIFIER;

path: PATH;

/*
 * Lexer rules.
 */

AT: '@';

BACK_SLASH: '\\';

COLON: ':';

COMMA: ',';

DASH: '-';

DOT: '.';

LPRAN: '(';

RPRAN: ')';

LBRAC: '{';

RBRAC: '}';

NUMBER: ( DIGIT )+;

SEMICOLON: ';';

SLASH: '/';

WHITESPACE: ( '\t' | ' ' | '\u000C' | '\n' | '\r' )+ { $channel = HIDDEN; };

UNDERSCORE: '_';

LT: '<';

GT: '>';

PATH: LT PATH_PART+ GT;

fragment PATH_PART:
  ~( LT | GT )
  ;

IDENTIFIER:
  IDENTIFIER_HEAD IDENETIFIER_TAIL*
  ;

fragment IDENETIFIER_TAIL:
  IDENTIFIER_HEAD
  | NUMBER
  ;

fragment IDENTIFIER_HEAD: ALPHABET | UNDERSCORE ;

fragment ALPHABET: 'A'..'Z' | 'a'..'z';

fragment DIGIT: '0'..'9';
