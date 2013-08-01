/*
 * Copyright (C) 2012, The Particle project authors.
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
 * @brief Some useful type traits.
 *
 * @author Soheil Hassas Yeganeh <soheil@cs.toronto.edu>
 * @version 0.1
 */

#ifndef CPP_PARTICLE_TYPE_TRAITS_H_
#define CPP_PARTICLE_TYPE_TRAITS_H_

#include <tuple>
#include <type_traits>
#include <utility>

namespace particle {

// Note: Since type traits are like functions for TMP, assume structs are
// functions, and don't follow the general style rules for classes and structs.

// The idea came from:
// http://stackoverflow.com/questions/11056714/c-type-traits-to-extract-template-parameter-class
template <typename T>
struct extract_value_type;

template <template<typename, typename...> class Container, typename ValueType,
    typename... Rest>
struct extract_value_type<Container<ValueType, Rest...>> {
  typedef ValueType value_type;
};

template <typename>
struct is_std_array : std::false_type {
};

template <typename T, std::size_t arr_size>
struct is_std_array<std::array<T, arr_size>> : std::true_type {
};

// Grabbed from the wheels library.
template <typename T, template <typename...> class Template>
struct is_specialization_of : std::false_type {};

template <template <typename...> class Template, typename... Args>
struct is_specialization_of<Template<Args...>, Template> : std::true_type {};

template <typename T>
struct is_tuple : is_specialization_of<T, std::tuple> {};

template <typename T>
struct is_pair : std::false_type {};

template <typename T1, typename T2>
struct is_pair<std::pair<T1, T2>> : std::true_type {};

}  // namespace particle

#endif  // CPP_PARTICLE_TYPE_TRAITS_H_

