/*
 * Copyright (C) 2012-2013, The Packet project authors.
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

/**
 * @file
 * @brief Exceptions in packet C++ runtime.
 *
 * @author soheil
 * @version 0.1
 */

#ifndef CPP_PACKET_EXCEPTIONS_H_
#define CPP_PACKET_EXCEPTIONS_H_

#include <stdexcept>
#include <string>

namespace packet {

class LibIoBootException : public ::std::runtime_error {
 public:
  explicit LibIoBootException(const ::std::string& what) : runtime_error(what) {
  }
};

class ConnectionException : public ::std::runtime_error {
 public:
  explicit ConnectionException(const ::std::string& what)
      : runtime_error(what) {}
};

class CorruptedDataException : public ::std::runtime_error {
 public:
  explicit CorruptedDataException(const ::std::string& what)
      : runtime_error(what) {}
};

class NotEnoughDataException : public ::std::runtime_error {
 public:
  explicit NotEnoughDataException(const ::std::string& what)
      : runtime_error(what) {}
};

class NotEnoughSpaceException : public ::std::runtime_error {
 public:
  explicit NotEnoughSpaceException(const ::std::string& what)
      : runtime_error(what) {}
};

class ListenerException : public ::std::runtime_error {
 public:
  explicit ListenerException(const ::std::string& what)
      : ::std::runtime_error(what) {}
};

}  // namespace packet

#endif  // CPP_PACKET_EXCEPTIONS_H_
