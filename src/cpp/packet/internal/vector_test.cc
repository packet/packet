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

#include <vector>
#include <thread>

#include "gtest/gtest.h"

#include "packet/internal/vector.h"

namespace packet {
namespace internal {

TEST(IoVector, PublicMethods) {
  const size_t VEC_SIZE = 128;
  auto shared_io_vector = make_shared_io_vector(VEC_SIZE);
  EXPECT_NE(nullptr, shared_io_vector);
  EXPECT_EQ(VEC_SIZE, shared_io_vector->size());
  EXPECT_NE(nullptr, shared_io_vector->get_buf());
}

TEST(IoVector, ThreadSafety) {
  std::vector<std::thread> threads;
  const size_t THREAD_COUNT = 100;
  const size_t VECTOR_PER_THREAD = 10000;
  const size_t VEC_SIZE = 128;

  auto shared_io_vector = make_shared_io_vector(VEC_SIZE);
  EXPECT_EQ(size_t(1), shared_io_vector->ref_count.load());

  for (size_t i = 0; i < THREAD_COUNT; i++) {
    threads.emplace_back([&shared_io_vector, VECTOR_PER_THREAD] {
      auto shared_io_vector_copy = shared_io_vector;
      std::vector<boost::intrusive_ptr<IoVector>> vectors;
      for (size_t i = 0; i < VECTOR_PER_THREAD; i++) {
        vectors.push_back(shared_io_vector_copy);
      }
    });
  }

  for (auto& th : threads) {
    th.join();
  }

  EXPECT_EQ(size_t(1), shared_io_vector->ref_count.load());
}

}  // namespace internal
}  // namespace packet

