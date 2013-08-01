/*
 * Copyright (C) 2012-2013, The Particle project authors.
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
 * @brief Common utilities for type names.
 *
 * Note: This only supports g++ and clang++.
 *
 * @author Soheil Hassas Yeganeh <soheil@cs.toronto.edu>
 * @version 0.1
 */

#ifndef CPP_PARTICLE_TYPENAME_H_
#define CPP_PARTICLE_TYPENAME_H_

#include <utility>
#include <string>
#include <typeinfo>

#include "boost/utility/string_ref.hpp"

namespace particle {

enum class TypeDelimiters : char {
  PAIR_SEP = ',',
  PAIR_BEG = '<',
  PAIR_END = '>',
};

std::string demangle_type(const char* type_name, bool drop_const = true);
std::string demangle_type(const std::type_info& type_id,
    bool drop_const = true);

template <typename T>
std::string demangle_type(bool drop_const = true) {
  return demangle_type(typeid(T), drop_const);
}

/**
 * Returns the string representation of a type. This representation is
 * garaunteed to be unique on all platforms.
 * @tparam T The c++ type.
 * @tparam drop_const Whether to drop const qualifier from type name.
 * @return The string representation of T.
 */
template <typename T, bool drop_const = true>
std::string type_name() {
  static auto tname = demangle_type<T>(drop_const);
  return tname;
}

/**
 * Returns the string representation of an object's type. This representation is
 * garaunteed to be unique on all platforms.
 * @param drop_const Whether to drop const qualifier from type name.
 * @return The string representation of the type.
 */
template <typename T, bool drop_const = true>
std::string type_name(const T& obj) {
  return demangle_type(typeid(obj), drop_const);
}

inline bool is_string(const std::string& t) {
  return t == type_name<std::string>();
}

inline bool is_integral(const std::string& t) {
  return t == type_name<int8_t>() || t == type_name<uint8_t>() ||
      t == type_name<int16_t>() || t == type_name<uint16_t>() ||
      t == type_name<int32_t>() || t == type_name<uint32_t>() ||
      t == type_name<int64_t>() || t == type_name<uint64_t>();
}

std::pair<boost::string_ref, boost::string_ref> get_pair_types(
    const std::string& t);

/**
 * @return Whether the type name represents a pair.
 */
inline bool is_pair_typename(const std::string& t) {
  auto pair_types = get_pair_types(t);
  return !pair_types.first.empty() && !pair_types.second.empty();
}

}  // namespace particle

#endif  // CPP_PARTICLE_TYPENAME_H_

