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

#include <utility>

#include "gmock/gmock.h"
#include "gtest/gtest.h"

#include "packet/packet.h"
#include "packet/vector.h"

#include "test/simple.h"
#include "test/including.h"

namespace packet {

using std::initializer_list;

template <typename Element>
void init_io_vector(IoVector* vector, initializer_list<Element> values) {
  size_t offset = 0;
  for (auto& value : values) {
    vector->write_data<Element>(value, offset);
    offset += sizeof(Element);
  }
}

IoVector make_packet_iov(size_t sections) {
  auto vector = make_io_vector(sections * (sections + 1) / 2);
  for (size_t i = 0; i < sections; i++) {
    size_t start = (i * (i + 1)) / 2;
    for (size_t j = 0; j <= i; j++) {
      vector.get_buf()[start + j] = static_cast<uint8_t>(i + 1);
    }
  }
  return vector;
}

TEST(PacketTest, Size) {
  const size_t k_vector_size = 13;
  auto io_vector = make_io_vector(k_vector_size);

  EXPECT_EQ(k_vector_size, io_vector.size());
}

TEST(PacketFactoryTest, DefaultSize) {
  const size_t k_sections = 13;
  auto io_vector = make_packet_iov(k_sections);

  auto factory = make_packet_factory<Packet, uint8_t>(0, false);
  auto packets = factory.read_packets(&io_vector, io_vector.size());

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
  const size_t k_sections = 13;
  auto io_vector = make_packet_iov(k_sections);

  auto factory = make_packet_factory<TestPacket>();
  auto packets = factory.read_packets(&io_vector, io_vector.size());

  EXPECT_EQ(k_sections, packets.size());
}

TEST(PacketFactoryTest, OutOfBoundReads) {
  for (size_t i = 1; i < 100; i++) {
    auto io_vector = make_io_vector(i);
    for (size_t j = 0; j < i - 1; j++) {
      io_vector.write_data<uint8_t>(1, j);
    }
    io_vector.write_data<uint8_t>(2, i - 1);

    auto factory = make_packet_factory<TestPacket>();
    auto packets = factory.read_packets(&io_vector, io_vector.size());

    EXPECT_EQ(size_t(i - 1), packets.size());
  }
}

TEST(PacketGeneratorTest, PacketSize) {
  const size_t k_sections = 13;
  auto io_vector = make_packet_iov(k_sections);

  EXPECT_EQ(static_cast<size_t>(1), simple::Simple::size_(io_vector));

  auto s = make_packet<simple::Simple>(io_vector);
  EXPECT_EQ(static_cast<uint8_t>(1), s.get_x());
}

TEST(PacketGeneratorTest, MakePacket) {
  const size_t k_sections = 3;
  auto io_vector = make_packet_iov(k_sections);

  EXPECT_EQ(static_cast<uint8_t>(1), io_vector.read_data<uint8_t>(0));
  EXPECT_EQ(static_cast<uint8_t>(2), io_vector.read_data<uint8_t>(1));
  auto inc_p = make_packet<including::AnotherIncluding>(io_vector);
  EXPECT_EQ(1, inc_p.get_c());
  EXPECT_EQ(2, inc_p.get_l());
  auto arr = inc_p.get_arr();
  EXPECT_EQ(2, arr[0]);
  EXPECT_EQ(3, arr[1]);
}

TEST(PacketGeneratorTest, MakePacketPolymorphic) {
  auto io_vector = make_io_vector(6);
  init_io_vector<uint8_t>(&io_vector, {1, 1, 2, 3, 1, 1});

  io_vector.consume(2);
  EXPECT_EQ(static_cast<uint8_t>(2), io_vector.read_data<uint8_t>(0));
  EXPECT_EQ(static_cast<uint8_t>(3), io_vector.read_data<uint8_t>(1));
  auto sp = make_packet<simple::SimpleParent>(io_vector);
  EXPECT_EQ(static_cast<uint8_t>(3), sp.get_l());
  auto i = including::cast_to_Including(sp);
  auto s_in_i = i.get_s();
  EXPECT_EQ(static_cast<uint8_t>(1), s_in_i.size());
}

TEST(PacketGeneratorTest, PacketInitilizer) {
  simple::Simple simple1(10);
  EXPECT_EQ(static_cast<uint8_t>(1), simple1.get_x());

  simple::AnotherSimple another_simple(10);
  EXPECT_EQ(static_cast<uint8_t>(1), another_simple.get_c());
  EXPECT_EQ(static_cast<uint8_t>(3), another_simple.get_l());

  simple::AnotherSimple another_simple2(100);
  EXPECT_EQ(static_cast<size_t>(3), another_simple2.size());

  simple::YetYetAnotherSimple yyanother_simple(100);
  EXPECT_EQ(static_cast<size_t>(3), yyanother_simple.size());
}

TEST(PacketGeneratorTest, AddCountedRepeatedField) {
  simple::YetAnotherSimple container(100);
  EXPECT_EQ(static_cast<size_t>(3), container.size());
  EXPECT_EQ(static_cast<uint8_t>(0), container.get_s());
  EXPECT_EQ(static_cast<size_t>(0), container.get_simples().size());

  simple::Simple simple1(10);
  container.add_simples(std::move(simple1));
  EXPECT_EQ(1, container.get_s());
  EXPECT_EQ(static_cast<size_t>(1), container.get_simples().size());

  simple::Simple simple2(10);
  container.add_simples(std::move(simple2));
  EXPECT_EQ(2, container.get_s());
  EXPECT_EQ(static_cast<size_t>(2), container.get_simples().size());
  EXPECT_EQ(static_cast<size_t>(5), container.size());
}

TEST(PacketGeneratorTest, AddImplicitlySizedRepeatedField) {
  simple::YetYetAnotherSimple yya_simple(100);
  EXPECT_EQ(static_cast<size_t>(3), yya_simple.size());
  EXPECT_EQ(0, yya_simple.get_s());
  EXPECT_EQ(static_cast<size_t>(0), yya_simple.get_a().size());

  simple::AnotherSimple a_simple1(10);
  auto a1_size = a_simple1.size();
  yya_simple.add_a(std::move(a_simple1));
  EXPECT_EQ(static_cast<size_t>(a1_size + 3), yya_simple.size());
  EXPECT_EQ(static_cast<int>(a1_size), yya_simple.get_s());
  EXPECT_EQ(static_cast<size_t>(1), yya_simple.get_a().size());

  simple::AnotherSimple a_simple2(10);
  auto a2_size = a_simple2.size();
  yya_simple.add_a(std::move(a_simple2));
  EXPECT_EQ(static_cast<size_t>(a1_size + a2_size + 3), yya_simple.size());
  EXPECT_EQ(static_cast<int>(a1_size + a2_size), yya_simple.get_s());
  EXPECT_EQ(static_cast<size_t>(2), yya_simple.get_a().size());
}

TEST(PacketGeneratorTest, ConstantSizedRepeatedField) {
  including::AnotherIncluding inc;
  EXPECT_EQ(static_cast<size_t>(4), inc.size());
  std::array<uint8_t, 2> w_arr = {{1, 2}};
  inc.set_arr(w_arr);
  w_arr = inc.get_arr();
  EXPECT_EQ(static_cast<size_t>(2), w_arr.size());
  EXPECT_EQ(static_cast<size_t>(1), w_arr[0]);
  EXPECT_EQ(static_cast<size_t>(2), w_arr[1]);
}

TEST(PacketGeneratorTest, Offset) {
  const size_t FIELD1_OFFSET = 4;
  const size_t FIELD2_OFFSET = 4 + 2 + 4;
  const uint16_t FIELD1_VAL = 0x1234;
  const uint16_t FIELD2_VAL = 0xabcd;

  simple::Offset offset;
  offset.set_offset_field1(FIELD1_VAL);
  offset.set_offset_field2(FIELD2_VAL);

  EXPECT_EQ(FIELD1_VAL,
            offset.get_io_vector()->read_data<uint16_t>(FIELD1_OFFSET));
  EXPECT_EQ(FIELD2_VAL,
            offset.get_io_vector()->read_data<uint16_t>(FIELD2_OFFSET));
}

}  // namespace packet

