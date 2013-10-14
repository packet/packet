/*
 * Copyright (C) 2012-2013, The Cyrus project authors.
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
 * @brief Unittests for packet.
 *
 * @author Soheil Hassas Yeganeh <soheil@cs.toronto.edu>
 * @version 0.1
 */

#include "gmock/gmock.h"
#include "gtest/gtest.h"

#include "packet/packet.h"
#include "packet/vector.h"

namespace packet {

IoVector make_packet_iov(size_t sections) {
  auto vector = make_io_vector(sections * (sections + 1) / 2);
  for (size_t i = 0; i < sections; i++) {
    size_t start = (i * (i + 1)) / 2;
    for (size_t j = 0; j <= i; j++) {
      vector.get_buf()[start + j] = uint8_t(i + 1);
    }
  }
  return vector;
}

TEST(PacketTest, Size) {
  auto const k_vector_size = size_t(13);
  auto io_vector = make_io_vector(k_vector_size);

  EXPECT_EQ(k_vector_size, io_vector.size());
}

TEST(PacketFactoryTest, DefaultSize) {
  auto const k_sections = size_t(13);
  auto io_vector = make_packet_iov(k_sections);

  auto factory = make_packet_factory<Packet, uint8_t>(0, false);
  auto packets = factory.read_packets(io_vector, io_vector.size());

  EXPECT_EQ(k_sections, packets.size());
}

class TestPacket : public Packet {
 public:
  explicit TestPacket(const IoVector& io_vector) : Packet(io_vector) {}

  static size_t size_(const IoVector& io_vector) {
    return io_vector.read_data<uint8_t>(0);
  }
};

TEST(PacketFactoryTest, PacketSize) {
  auto const k_sections = size_t(13);
  auto io_vector = make_packet_iov(k_sections);

  auto factory = make_packet_factory<TestPacket>();
  auto packets = factory.read_packets(io_vector, io_vector.size());

  EXPECT_EQ(k_sections, packets.size());
}

}  // namespace packet

