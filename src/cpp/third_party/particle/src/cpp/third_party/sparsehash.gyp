#
# Copyright (C) 2013, The Particle project authors.
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

{
  'variables': {
    'sparse_hash_home': 'sparsehash',
    'sparse_hash_src_home': '<(sparse_hash_home)/src',
  },
  'targets': [
    {
      'target_name': 'sparsehash',
      'type': 'none',
      'all_dependent_settings': {
        'include_dirs': [
          '<(sparse_hash_src_home)',
        ],
      },
      'include_dirs': [
        '<(sparse_hash_src_home)',
      ],
      'defines': [
        'HAVE_CONFIG_H',
      ],
    },
  ]
}
