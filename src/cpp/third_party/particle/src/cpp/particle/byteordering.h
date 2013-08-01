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
 * @brief Provides byte ordering routines.
 *
 * @author soheil
 * @version 0.1
 */


#ifndef CPP_PARTICLE_BYTEORDERING_H_
#define CPP_PARTICLE_BYTEORDERING_H_

#include <arpa/inet.h>

#include <cstdint>

namespace particle {

#if __BYTE_ORDER == __BIG_ENDIAN
#define ntohll(x) (x)
#define htonll(x) (x)
#else
#if __BYTE_ORDER == __LITTLE_ENDIAN
#define ntohll(x) (((uint64_t) htonl(x) << 32) | htonl(x >> 32))
#define htonll(x) (((uint64_t) htonl(x) << 32) | htonl(x >> 32))
#endif
#endif

template <typename T>
T ntohxx(T data);

template <typename T>
T htonxx(T data);

template <>
inline char ntohxx<char>(char data) {
  return data;
}

template <>
inline char htonxx<char>(char data) {
  return data;
}

template <>
inline uint8_t ntohxx<uint8_t>(uint8_t data) {
  return data;
}

template <>
inline uint8_t htonxx<uint8_t>(uint8_t data) {
  return data;
}

template <>
inline uint16_t ntohxx<uint16_t>(uint16_t data) {
  return ntohs(data);
}

template <>
inline uint16_t htonxx<uint16_t>(uint16_t data) {
  return htons(data);
}

template <>
inline uint32_t ntohxx<uint32_t>(uint32_t data) {
  return ntohl(data);
}

template <>
inline uint32_t htonxx<uint32_t>(uint32_t data) {
  return htonl(data);
}

template <>
inline uint64_t ntohxx<uint64_t>(uint64_t data) {
  return ntohll(data);
}

template <>
inline uint64_t htonxx<uint64_t>(uint64_t data) {
  return htonll(data);
}

#undef htonll

}  // namespace particle

#endif  // CPP_PARTICLE_BYTEORDERING_H_

