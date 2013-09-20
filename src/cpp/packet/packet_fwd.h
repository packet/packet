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
 * @brief Forward decleration for packet C++ io lib.
 *
 * @author Soheil Hassas Yeganeh <soheil@cs.toronto.edu>
 * @version 0.1
 */

#ifndef CPP_PACKET_PACKET_FWD_H_
#define CPP_PACKET_PACKET_FWD_H_

#include "packet/internal/packet_fwd.h"

namespace packet {

class IoVector;
class Packet;

template <typename Packet>
class Channel;

template <typename Packet>
std::shared_ptr<Packet> make_packet(const IoVector& io_vec);

template <typename Packet>
std::shared_ptr<Packet> make_packet(size_t size);

IoVector make_io_vector(size_t size);
IoVector make_io_vector(
    const std::shared_ptr<packet::internal::IoVector>& shared_io_vector);

}  // namespace packet

#endif  // CPP_PACKET_PACKET_FWD_H_

