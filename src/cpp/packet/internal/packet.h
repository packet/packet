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
 * @brief Internal utilities for packet.
 *
 * @author Soheil Hassas Yeganeh <soheil@cs.toronto.edu>
 * @version 0.1
 */

#ifndef CPP_PACKET_INTERNAL_PACKET_H_
#define CPP_PACKET_INTERNAL_PACKET_H_

#include "packet/internal/packet_fwd.h"
#include "packet/packet_fwd.h"

namespace packet {
namespace internal {

template <typename DataT>
inline typename ::std::enable_if<std::is_base_of<Packet, DataT>::value,
    size_t>::type get_data_size(const packet::IoVector& vec) {
  return DataT::size_(vec);
}

template <typename DataT>
inline typename ::std::enable_if<std::is_integral<DataT>::value, size_t>::type
    get_data_size(const packet::IoVector& vec) {
  return sizeof(DataT);
}

}  // namespace internal
}  // namespace packet

#endif  // CPP_PACKET_INTERNAL_PACKET_H_

