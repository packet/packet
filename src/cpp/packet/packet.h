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
 * @brief Packet base class and packet factory.
 *
 * @author Soheil Hassas Yeganeh <soheil@cs.toronto.edu>
 * @version 0.1
 */

#ifndef CPP_PACKET_PACKET_H_
#define CPP_PACKET_PACKET_H_

#include <vector>
#include <utility>

#include "particle/byteordering.h"

#include "packet/vector.h"

namespace packet {

/** The base class of all packets. */
class Packet {
 public:
  typedef IoVector::MetaData MetaData;

  explicit Packet(const IoVector& io_vector) : vector(io_vector) {}
  explicit Packet(IoVector&& io_vector) : vector(std::move(io_vector)) {}

  Packet(const Packet&) = default;
  Packet(Packet&&) = default;

  Packet& operator=(const Packet&) = default;
  Packet& operator=(Packet&&) = default;

  virtual ~Packet() {}

  virtual size_t size() const {
    return vector.size();
  }

  const IoVector* get_io_vector() const {
    return &vector;
  }

  IoVector* get_io_vector() {
    return &vector;
  }

  MetaData get_metadata() const { return vector.get_metadata(); }

  void set_metadata(MetaData md) { vector.set_metadata(md); }

 protected:
  IoVector vector;
};

template <typename Packet>
std::shared_ptr<Packet> make_packet(const IoVector& io_vec) {
  auto packet = std::make_shared<Packet>(io_vec);
  return packet;
}

template <typename Packet>
std::shared_ptr<Packet> make_packet(size_t size) {
  return make_packet<Packet>(make_io_vector(size));
}

template <typename Packet>
class PacketFactory final {
 public:
  typedef std::shared_ptr<Packet> PacketPtr;
  typedef std::vector<PacketPtr> PacketVector;

  void read_packets(IoVector io_vec, size_t data_size,
      PacketVector* packets, size_t* consumed) {
    while (*consumed < data_size) {
      try {
        auto size = size_reader(io_vec);

        if (unlikely(size == 0)) {
          // T(soheil): This should be an indication of error.
          break;
        }

        if (data_size < size + *consumed) {
          break;
        }

        packets->push_back(make_packet<Packet>(io_vec));
        io_vec.consume(size);
        *consumed += size;
      } catch(NotEnoughDataException& e) {  // NOLINT
        break;
      }
    }
  }

  PacketVector read_packets(IoVector io_vec, size_t data_size) {
    PacketVector packets;
    size_t consumed = 0;
    read_packets(io_vec, data_size, &packets, &consumed);
    return packets;
  }

 private:
  explicit PacketFactory(std::function<size_t(const IoVector&)> size_reader)
      : size_reader(size_reader) {}

  std::function<size_t(const IoVector&)> size_reader;

  template <typename P>
  friend PacketFactory<P> make_packet_factory(
      std::function<size_t(const IoVector&)> size_reader);
};

template <typename Size>
size_t default_size_reader(const IoVector& io_vec, size_t size_offset,
    bool big_endian) {
  static_assert(sizeof(Size) <= 4,
      "Packet does not support size fields of more than 32 bits.");

  auto size = io_vec.read_data<Size>(size_offset);
  if (big_endian) {
    size = particle::ntohxx(size);
  }

  if (size < sizeof(Size)) {
    throw CorruptedDataException(
        "default_size_reader: Size is smaller than Size!");
  }
  return size;
}

template <typename Packet>
PacketFactory<Packet> make_packet_factory(
    std::function<size_t(const IoVector&)> size_reader) {
  return PacketFactory<Packet>(size_reader);
}

template <typename Packet, typename Size>
PacketFactory<Packet> make_packet_factory(size_t size_offset,
    bool big_endian = false) {
  return make_packet_factory<Packet>(bind(default_size_reader<Size>,
        std::placeholders::_1, size_offset, big_endian));
}

template <typename Packet>
PacketFactory<Packet> make_packet_factory() {
  return make_packet_factory<Packet>([] (const IoVector& io_vector) -> size_t {
        return Packet::size_(io_vector);
      });
}

}  // namespace packet

#endif  // CPP_PACKET_PACKET_H_

