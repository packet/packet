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

#include <chrono>
#include <functional>
#include <thread>

#include "packet/vector.h"

#include "gmock/gmock.h"
#include "gtest/gtest.h"

namespace packet {

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
  auto const size = size_t(13);
  auto io_vector = make_iov(13);

  EXPECT_EQ(size, io_vector.size());
}

TEST(IoVectorTest, MemCopy) {
  auto const src_size = size_t(4 + 3 + 2 + 1);
  auto const src_voff = uint8_t(1);
  auto src_io_vector = make_iov(src_size, src_voff);

  auto const dst_size = size_t(3 + 2 + 1);
  auto const dst_voff  = uint8_t(2);
  auto dst_io_vector = make_iov(dst_size, dst_voff);

  EXPECT_EQ(src_size, src_io_vector.size());
  EXPECT_EQ(dst_size, dst_io_vector.size());

  IoVector::memmove(&dst_io_vector, 0, &src_io_vector, 0, 0);

  for (size_t i = 0; i < src_size; i++) {
    EXPECT_EQ(uint8_t(i + src_voff), src_io_vector.read_data<uint8_t>(i));
  }

  for (size_t i = 0; i < dst_size; i++) {
    EXPECT_EQ(uint8_t(i + dst_voff), dst_io_vector.read_data<uint8_t>(i));
  }

  IoVector::memmove(&dst_io_vector, 0, &src_io_vector, 0, src_io_vector.size());

  for (size_t i = 0; i < dst_size; i++) {
    EXPECT_EQ(uint8_t(i + src_voff), dst_io_vector.read_data<uint8_t>(i));
  }

  auto const copy_offset = size_t(2);
  IoVector::memmove(&dst_io_vector, copy_offset,
      &src_io_vector, 0, src_io_vector.size());

  for (size_t i = 0; i < copy_offset; i++) {
    EXPECT_EQ(uint8_t(i + src_voff), dst_io_vector.read_data<uint8_t>(i));
  }

  for (size_t i = copy_offset; i < dst_size; i++) {
    EXPECT_EQ(uint8_t(i + src_voff - copy_offset),
        dst_io_vector.read_data<uint8_t>(i));
  }
}

TEST(IoVectorTest, BoundChecks) {
  auto const size = size_t(13);
  auto io_vector = make_iov(size);

  for (size_t i = 0; i < size; i++) {
    EXPECT_TRUE(io_vector.resides_in_buffer(i, size - i));
    EXPECT_FALSE(io_vector.resides_in_buffer(i, size - i + 1));
  }
}

TEST(IoVectorTest, ReadSimpleData) {
  auto const size = size_t(13);
  auto io_vector = make_iov(size);

  for (size_t i = 0; i < size; i++) {
    uint8_t data = io_vector.read_data<uint8_t>(i);
    EXPECT_EQ(i + 1, data);
  }
}

TEST(IoVectorTest, ReadAndConsume) {
  auto const size = size_t(13);
  auto io_vector = make_iov(size);

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
  auto const size = size_t(13);
  auto io_vector = make_iov(size);

  io_vector.consume(size);
  EXPECT_EQ(size, io_vector.offset);
}

TEST(IoVectorTest, OverConsume) {
  auto const size = size_t(13);
  auto io_vector = make_iov(size);

  EXPECT_THROW(io_vector.consume(size + 1), NotEnoughDataException);
}

}  // namespace packet

