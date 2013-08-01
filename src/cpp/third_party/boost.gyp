#
# Copyright (C) 2012-2013, The Particle project authors.
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
    'boost_home': 'boost',
  },
  'targets': [
    {
      'target_name': 'boost_common',
      'type': 'none',
      'all_dependent_settings': {
        'include_dirs': [
          '<(boost_home)',
        ],
      },
    },
    {
      'target_name': 'boost_smartptr',
      'type': '<(library)',
      'dependencies': [
        ':boost_common',
      ],
      'sources': [
        '<(boost_home)/libs/smart_ptr/src/sp_collector.cpp',
        '<(boost_home)/libs/smart_ptr/src/sp_debug_hooks.cpp',
      ],
    },
    {
      'target_name': 'boost_system',
      'type': '<(library)',
      'dependencies': [
        ':boost_common',
      ],
      'sources': [
        '<(boost_home)/libs/system/src/error_code.cpp',
        '<(boost_home)/libs/system/src/local_free_on_destruction.hpp',
      ],
    },
    {
      'target_name': 'boost_fs',
      'type': '<(library)',
      'include_dirs': [
        '<(boost_home)/libs',
      ],
      'dependencies': [
        ':boost_common',
        ':boost_system',
      ],
      'sources': [
        '<(boost_home)/libs/filesystem/src/codecvt_error_category.cpp',
        '<(boost_home)/libs/filesystem/src/operations.cpp',
        '<(boost_home)/libs/filesystem/src/path_traits.cpp',
        '<(boost_home)/libs/filesystem/src/path.cpp',
        '<(boost_home)/libs/filesystem/src/portability.cpp',
        '<(boost_home)/libs/filesystem/src/unique_path.cpp',
        '<(boost_home)/libs/filesystem/src/utf8_codecvt_facet.cpp',
        '<(boost_home)/libs/filesystem/src/windows_file_codecvt.cpp',
        '<(boost_home)/libs/filesystem/src/windows_file_codecvt.hpp',
      ],
    },
  ]
}
