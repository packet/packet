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
    'glog_home': 'glog',
    'glog_src_home': '<(glog_home)/src',
  },
  'targets': [
    {
      'target_name': 'glog',
      'type': '<(library)',
      'include_dirs': [
        '<(glog_src_home)',
      ],
      'dependencies': [
        'gflags.gyp:gflags',
      ],
      'all_dependent_settings': {
        'include_dirs': [
          '<(glog_src_home)',
        ],
      },
      'sources': [
        '<(glog_src_home)/config.h',
        '<(glog_src_home)/stacktrace_libunwind-inl.h',
        '<(glog_src_home)/utilities.cc',
        '<(glog_src_home)/glog/raw_logging.h',
        '<(glog_src_home)/glog/vlog_is_on.h',
        '<(glog_src_home)/glog/stl_logging.h',
        '<(glog_src_home)/glog/logging.h',
        '<(glog_src_home)/glog/log_severity.h',
        '<(glog_src_home)/vlog_is_on.cc',
        '<(glog_src_home)/logging.cc',
        '<(glog_src_home)/utilities.h',
        '<(glog_src_home)/mock-log.h',
        '<(glog_src_home)/symbolize.cc',
        '<(glog_src_home)/demangle.cc',
        '<(glog_src_home)/linux/config.h',
        '<(glog_src_home)/base/mutex.h',
        '<(glog_src_home)/base/commandlineflags.h',
        '<(glog_src_home)/base/googleinit.h',
        '<(glog_src_home)/stacktrace_powerpc-inl.h',
        '<(glog_src_home)/signalhandler.cc',
        '<(glog_src_home)/stacktrace_generic-inl.h',
        '<(glog_src_home)/stacktrace_x86-inl.h',
        '<(glog_src_home)/raw_logging.cc',
        '<(glog_src_home)/symbolize.h',
        '<(glog_src_home)/stacktrace_x86_64-inl.h',
        '<(glog_src_home)/stacktrace.h',
        '<(glog_src_home)/demangle.h',
      ],
    },
  ]
}
