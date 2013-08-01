/*
 * Copyright (C) 2013, The Cyrus project authors.
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
 * @brief Provides basic binary manipulation routines.
 *
 * @author Soheil Hassas Yeganeh <soheil@cs.toronto.edu>
 * @version 0.1
 */

#ifndef CPP_PARTICLE_BITHACKS_H_
#define CPP_PARTICLE_BITHACKS_H_

#include <cstdint>

namespace particle {

/**
 * Shifts and or's the number recursively. For instance if 
 * @param n The number.
 * @param p The power.
 * @tparam T n's type.
 */
template <typename T>
constexpr T shift_or(T n, uint8_t p) {
  return p == 0 ? n : shift_or(n, p >> 1) | (shift_or(n, p >> 1) >> p);
}

// Adopted from the 32-bit version in:
// http://graphics.stanford.edu/~seander/bithacks.html#RoundUpPowerOf2
/** Rounds an integer to the next highest power of 2 number. */
template <typename T>
constexpr T round_to_power_of_two(T n);

template <>
constexpr uint8_t round_to_power_of_two<uint8_t>(uint8_t n) {
  return shift_or(n - 1, 8 >> 1) + 1;
}

template <>
constexpr uint16_t round_to_power_of_two<uint16_t>(uint16_t n) {
  return shift_or(n - 1, 16 >> 1) + 1;
}

template <>
constexpr uint32_t round_to_power_of_two<uint32_t>(uint32_t n) {
  return shift_or(n - 1, 32 >> 1) + 1;
}

template <>
constexpr uint64_t round_to_power_of_two<uint64_t>(uint64_t n) {
  return shift_or(n - 1, 64 >> 1) + 1;
}

}  // namespace particle

#endif  // CPP_PARTICLE_BITHACKS_H_

