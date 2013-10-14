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
 * @brief Unittests for IO vector.
 *
 * @author Soheil Hassas Yeganeh <soheil@cs.toronto.edu>
 * @version 0.1
 */

#include <cstdint>

#include <array>
#include <chrono>
#include <functional>
#include <thread>

#include "packet/packet.h"
#include "packet/vector.h"

#include "gmock/gmock.h"
#include "gtest/gtest.h"

namespace packet {

using std::array;
using std::bind;
using std::placeholders::_1;

IoVector make_iov(size_t size, uint8_t value_offset = 1) {
  auto vector = make_io_vector(size);
  for (size_t i = 0; i < size; i++) {
    vector.get_buf()[i] = uint8_t(i + value_offset);
  }
  return vector;
}

TEST(IoVectorTest, GetSize) {
  auto const k_vector_size = size_t(13);
  auto io_vector = make_iov(k_vector_size);

  EXPECT_EQ(k_vector_size, io_vector.size());
}

TEST(IoVectorTest, MemCopy) {
  auto const k_src_size = size_t(4 + 3 + 2 + 1);
  auto const src_voff = uint8_t(1);
  auto src_io_vector = make_iov(k_src_size, src_voff);

  auto const k_dst_size = size_t(3 + 2 + 1);
  auto const dst_voff  = uint8_t(2);
  auto dst_io_vector = make_iov(k_dst_size, dst_voff);

  EXPECT_EQ(k_src_size, src_io_vector.size());
  EXPECT_EQ(k_dst_size, dst_io_vector.size());

  IoVector::memmove(&dst_io_vector, 0, &src_io_vector, 0, 0);

  for (size_t i = 0; i < k_src_size; i++) {
    EXPECT_EQ(uint8_t(i + src_voff), src_io_vector.read_data<uint8_t>(i));
  }

  for (size_t i = 0; i < k_dst_size; i++) {
    EXPECT_EQ(uint8_t(i + dst_voff), dst_io_vector.read_data<uint8_t>(i));
  }

  IoVector::memmove(&dst_io_vector, 0, &src_io_vector, 0, src_io_vector.size());

  for (size_t i = 0; i < k_dst_size; i++) {
    EXPECT_EQ(uint8_t(i + src_voff), dst_io_vector.read_data<uint8_t>(i));
  }

  auto const copy_offset = size_t(2);
  IoVector::memmove(&dst_io_vector, copy_offset,
      &src_io_vector, 0, src_io_vector.size());

  for (size_t i = 0; i < copy_offset; i++) {
    EXPECT_EQ(uint8_t(i + src_voff), dst_io_vector.read_data<uint8_t>(i));
  }

  for (size_t i = copy_offset; i < k_dst_size; i++) {
    EXPECT_EQ(uint8_t(i + src_voff - copy_offset),
        dst_io_vector.read_data<uint8_t>(i));
  }
}

TEST(IoVectorTest, BoundChecks) {
  auto const k_vector_size = size_t(13);
  auto io_vector = make_iov(k_vector_size);

  for (size_t i = 0; i < k_vector_size; i++) {
    EXPECT_TRUE(io_vector.resides_in_buffer(i, k_vector_size - i));
    EXPECT_FALSE(io_vector.resides_in_buffer(i, k_vector_size - i + 1));
  }
}

TEST(IoVectorTest, ReadSimpleData) {
  auto const k_vector_size = size_t(13);
  auto io_vector = make_iov(k_vector_size);

  for (size_t i = 0; i < k_vector_size; i++) {
    uint8_t data = io_vector.read_data<uint8_t>(i);
    EXPECT_EQ(i + 1, data);
  }
}

TEST(IoVectorTest, ReadAndConsume) {
  auto const k_vector_size = size_t(13);
  auto io_vector = make_iov(k_vector_size);

  uint16_t expected_16 = 0x0504;
  uint32_t expected_32 = 0x06050403;

  uint16_t data16 = io_vector.read_data<uint16_t>(3);
  EXPECT_EQ(expected_16, data16);
  uint32_t data32 = io_vector.read_data<uint32_t>(2);
  EXPECT_EQ(expected_32, data32);

  io_vector.consume(1);

  data16 = io_vector.read_data<uint16_t>(2);
  EXPECT_EQ(expected_16, data16);
  data32 = io_vector.read_data<uint32_t>(1);
  EXPECT_EQ(expected_32, data32);

  io_vector.consume(1);

  data16 = io_vector.read_data<uint16_t>(1);
  EXPECT_EQ(expected_16, data16);
  data32 = io_vector.read_data<uint32_t>(0);
  EXPECT_EQ(expected_32, data32);

  io_vector.consume(3);

  expected_16 = 0x0807;
  expected_32 = 0x09080706;
  data16 = io_vector.read_data<uint16_t>(1);
  EXPECT_EQ(expected_16, data16);
  data32 = io_vector.read_data<uint32_t>(0);
  EXPECT_EQ(expected_32, data32);

  EXPECT_THROW(io_vector.read_data<uint8_t>(10), NotEnoughDataException);
}

TEST(IoVectorTest, Consume) {
  auto const k_vector_size = size_t(13);
  auto io_vector = make_iov(k_vector_size);

  io_vector.consume(k_vector_size);
  EXPECT_EQ(k_vector_size, io_vector.offset);
}

TEST(IoVectorTest, OverConsume) {
  auto const k_vector_size = size_t(13);
  auto io_vector = make_iov(k_vector_size);

  EXPECT_THROW(io_vector.consume(k_vector_size + 1), NotEnoughDataException);
}

TEST(IoVectorTest, WriteIntegralData) {
  typedef size_t Element;

  auto const k_element_count  = uint8_t(10);
  auto const k_element_size = uint8_t(sizeof(Element));
  auto const k_vector_size = k_element_count * k_element_size;

  auto io_vector = make_io_vector(k_vector_size);

  for (auto i = Element(0); i < k_element_count; i++) {
    io_vector.write_data(i, i * k_element_size);
  }

  for (auto i = Element(0); i < k_element_count; i++) {
    EXPECT_EQ(i, io_vector.read_data<Element>(i * k_element_size));
  }
}

TEST(IoVectorTest, WriteArray) {
  typedef size_t Element;

  auto const k_element_count  = uint8_t(10);
  auto const k_element_size = uint8_t(sizeof(Element));
  auto const k_vector_size = k_element_count * k_element_size;

  std::array<Element, k_element_count> data;
  for (auto i = Element(0); i < k_element_count; i++) {
    data[i] = i;
  }

  auto io_vector = make_io_vector(k_vector_size);
  io_vector.write_data(data);

  EXPECT_EQ(data, io_vector.read_data<decltype(data)>());
}

class TestPacket : public Packet {
 public:
  explicit TestPacket(const IoVector& io_vector) : Packet(io_vector) {}

  static size_t size_(const IoVector& io_vector) {
    return io_vector.read_data<uint8_t>(0);
  }

  size_t size() const { return size_(*get_io_vector()); }
  void set_size(size_t size) { get_io_vector()->write_data<uint8_t>(size, 0); }

  static const size_t PACKET_SIZE;
};

const size_t TestPacket::PACKET_SIZE = sizeof(uint8_t);

TEST(IoVectorTest, WritePacket) {
  TestPacket packet(make_io_vector(TestPacket::PACKET_SIZE));
  packet.set_size(TestPacket::PACKET_SIZE);

  auto io_vector = make_io_vector(TestPacket::PACKET_SIZE);
  io_vector.write_data(packet);

  auto read_packet = io_vector.read_data<TestPacket>();
  EXPECT_EQ(TestPacket::PACKET_SIZE, read_packet.size());
}

// TODO(soheil): Adds tests for repeated data.

}  // namespace packet

