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
''' Provides utilities for packet packages (e.g. packet path). '''

__author__ = 'Soheil Hassas Yeganeh <soheil@cs.toronto.edu>'

import os
from os import path

__PACKET_PATH_ENV_VARIABLE = 'PACKET_PATH'
__PACKET_PATH_SEPARATOR = ':'

def get_packet_path(packet_path=None):
  ''' Parses the PACKET_PATH variable, and returns a list of them.
      @param packet_path: The PACKET_PATH. If None, or empty it will use the
                          PACKET_PATH environment variable. If the env variable
                          is empty, it will use current directory. '''
  # Use the environment variable.
  if not packet_path:
    packet_path = os.environ.get(__PACKET_PATH_ENV_VARIABLE)

  # If none are set the default packet path is used.
  if not packet_path:
    packet_path = os.getcwd()

  valid_repo_paths = []
  for repo_path in packet_path.split(__PACKET_PATH_SEPARATOR):
    # Throw out invalid paths for the sake of efficiency.
    if path.exists(repo_path):
      valid_repo_paths.append(path.abspath(repo_path))
  return valid_repo_paths

def search_for_packet(packet_file, repo_paths):
  ''' Searches for a packet file in the repository paths. '''
  for repo_path in repo_paths:
    potential_file_path = path.join(repo_path, packet_file)
    if path.exists(potential_file_path) and path.isfile(potential_file_path):
      return potential_file_path
  return None
