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
''' Basic generator classes. '''

__author__ = 'Soheil Hassas Yeganeh <soheil@cs.toronto.edu>'

from packet.generator.c import CGenerator

__GENERATORS = {
                'c': CGenerator,
                # TODO(soheil): Implmenet this.
                'cpp': None,
                'java': None,
                'python': None,
                }

def supported_languages():
  ''' Returns the list of supported languages. '''
  return __GENERATORS.keys()

def get_generator(lang):
  ''' Returns the generator of a specific language.
      @param lang The language. '''
  return __GENERATORS.get(lang)
