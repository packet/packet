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
 * @brief Unit tests for SharedIoVector.
 *
 * @author Soheil Hassas Yeganeh <soheil@cs.toronto.edu>
 * @version 0.1
 */

#include "gtest/gtest.h"

#include "packet/internal/vector.h"

namespace packet {
namespace internal {

TEST(IoVector, PublicMethods) {
  const size_t vec_size = 128;
  auto shared_io_vector = make_shared_io_vector(vec_size);
  EXPECT_NE(nullptr, shared_io_vector);
  EXPECT_EQ(vec_size, shared_io_vector->size());
  EXPECT_NE(nullptr, shared_io_vector->get_buf());
}

}  // namespace internal
}  // namespace packet

