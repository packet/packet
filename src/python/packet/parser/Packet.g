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
  ASTLabelType=CommonTree;
}

tokens {
  ANNOTATION;
  ANNOTATION_PARAM;
  EXTENDS;
  FIELD;
  FIELD_TYPE;
  FILE;
  INCLUDE;
  PACKAGE;
  PACKET;
  SEQUENCE;
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
    parser.file()
  except RecognitionException:
    traceback.print_stack()
}

/*
 * Parser rules.
 */
file:
  package* expr+ -> ^(FILE package* expr+);

package:
  'package' name literal SEMICOLON -> ^(PACKAGE name literal);

expr:
  include
  | packet;

include:
  'include' path SEMICOLON -> ^(INCLUDE path)
  ;

packet:
  packet_def LBRAC packet_body RBRAC -> ^(PACKET packet_def packet_body)
  ;

packet_def:
  annotation* 'packet' packet_name parent_packet? ->
      packet_name annotation* parent_packet?
  ;

parent_packet:
  LEFT_PRANTHESIS parent_packet_name RIGHT_PRANTHESIS ->
      ^(EXTENDS parent_packet_name)
  ;

parent_packet_name:
  ( packet_name DOT )? packet_name
  | 'object';

packet_body:
   (field SEMICOLON!)*
   ;

field:
  annotation* field_type field_name ->
      ^(FIELD field_name annotation* field_type)
  ;

annotation:
  AT IDENTIFIER annotation_params -> ^(ANNOTATION IDENTIFIER annotation_params)
  ;

annotation_params:
  LEFT_PRANTHESIS annotation_param ( COMMA annotation_param)* RIGHT_PRANTHESIS;

annotation_param:
  IDENTIFIER (EQ value)? -> ^(ANNOTATION_PARAM IDENTIFIER value?)
  ;

packet_name: IDENTIFIER;

field_name: IDENTIFIER;

field_type: ( IDENTIFIER DOT )? IDENTIFIER ->
    ^(FIELD_TYPE IDENTIFIER IDENTIFIER? );

name: IDENTIFIER;

value: literal | NUMBER;

literal: LITERAL;

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

LEFT_PRANTHESIS: '(';

RIGHT_PRANTHESIS: ')';

LBRAC: '{';

RBRAC: '}';

SEMICOLON: ';';

SLASH: '/';

WHITESPACE: ( '\t' | ' ' | '\u000C' | '\n' | '\r' )+ { $channel = HIDDEN; };

UNDERSCORE: '_';

LT: '<';

GT: '>';

EQ: '=';

NUMBER:
  ( DASH? ( DIGIT+ (DOT DIGIT+)? ) ) | ( '0x' ( DIGIT | 'A'..'F' | 'a'..'f' )+ )
  ;

LITERAL: QOUTATION LITERAL_PART+ QOUTATION;

fragment LITERAL_PART:
  ~( QOUTATION )
  ;
  
fragment QOUTATION:
  '"' | '\''
  ;

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
