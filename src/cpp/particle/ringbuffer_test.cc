/*
 * Copyright (C) 2012, The Cyrus project authors.
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
 * @brief Unit test for the lockless ring buffer.
 *
 * @author Soheil Hassas Yeganeh <soheil@cs.toronto.edu>
 * @version 0.1
 */

#include <atomic>
#include <future>
#include <memory>
#include <string>
#include <thread>
#include <vector>

#include "gtest/gtest.h"

#include "particle/bithacks.h"
#include "particle/cpu.h"
#include "particle/ringbuffer.h"

namespace particle {

using std::async;
using std::atomic;
using std::future;
using std::make_shared;
using std::string;
using std::thread;
using std::vector;

TEST(RingBuffer, SingleThreadedTest) {
  const size_t capacity = 128;
  RingBuffer<int> ring_buffer(capacity);
  ASSERT_EQ(round_to_power_of_two(capacity), ring_buffer.capacity());
  ASSERT_EQ(round_to_power_of_two(capacity), ring_buffer.guess_free_space());
  ASSERT_EQ(size_t(0), ring_buffer.guess_size());

  for (size_t i = 0; i < capacity - 1; i++) {
    ASSERT_TRUE(ring_buffer.try_write(1));
  }
  ASSERT_FALSE(ring_buffer.try_write(1));

  for (size_t i = 0; i < capacity - 1; i++) {
    int element = 0;
    ASSERT_TRUE(ring_buffer.try_read(&element));
    ASSERT_EQ(1, element);
  }

  ASSERT_FALSE(ring_buffer.try_read());

  for (size_t i = 0; i< capacity - 2; i++) {
     ASSERT_TRUE(ring_buffer.try_write(1));
  }

  for (size_t i = 0; i < capacity * 10; i++) {
    ASSERT_TRUE(ring_buffer.try_write(1));

    int element = 0;
    ASSERT_TRUE(ring_buffer.try_read(&element));
    ASSERT_EQ(1, element);
  }

  for (size_t i = 0; i< capacity - 2; i++) {
    int element = 0;
    ASSERT_TRUE(ring_buffer.try_read(&element));
    ASSERT_EQ(1, element);
  }
}

struct BufferElement {
  BufferElement() : destructed_before(0) {}

  BufferElement(const BufferElement& that) : destructed_before(0) {
    assert(that.destructed_before.load() == 0);
    assert(destructed_before.load() == 0);
  }

  BufferElement& operator=(const BufferElement& that) {
    assert(that.destructed_before.load() == 0);
    destructed_before.store(0);
    return *this;
  }

  ~BufferElement() {
    if (destructed_before++ != 0) {
      throw std::runtime_error("Object destructed before");
    }
  }

  atomic<size_t> destructed_before;
  char padding1[128-sizeof(destructed_before)];
};

TEST(RingBuffer, MultipleAsyncs) {
  const size_t capacity = 100;
  const size_t number_of_msgs = 300;
  atomic<size_t> msg_count(0);

  RingBuffer<int> ring_buffer(capacity);
  vector<future<void>> futures;

  for (size_t i = 0; i < number_of_msgs; i++) {
    futures.push_back(async([&] {
          while (!ring_buffer.try_write(1)) {}
          msg_count++;
        }));
    futures.push_back(async([&] {
          while (!ring_buffer.try_read()) {}
          msg_count--;
        }));
  }

  for (auto& f : futures) { f.get(); }
  ASSERT_EQ(size_t(0), ring_buffer.guess_size());
  ASSERT_EQ(round_to_power_of_two(capacity), ring_buffer.guess_free_space());
  ASSERT_EQ(size_t(0), msg_count.load());
}

template <bool multiple_entrance>
void test_multiple_threads(const size_t capacity,
    const size_t number_of_threads, const size_t number_of_msg_per_thread) {
  atomic<size_t> msg_count(0);

  RingBuffer<BufferElement, multiple_entrance> ring_buffer(capacity);
  vector<thread> wthreads;
  vector<thread> rthreads;

  for (size_t i = 0; i < number_of_threads; i++) {
    wthreads.emplace_back([&] {
        for (size_t j = 0; j < number_of_msg_per_thread; j++) {
          while (!ring_buffer.try_write(BufferElement())) {}
          msg_count++;
        }
      });
  }
  for (size_t i = 0; i < number_of_threads; i++) {
    rthreads.emplace_back([&] {
        for (size_t j = 0; j < number_of_msg_per_thread; j++) {
          while (!ring_buffer.try_read()) {}
          msg_count--;
        }
      });
  }
  for (auto& thread : wthreads) { thread.join(); }
  for (auto& thread : rthreads) { thread.join(); }

  ASSERT_EQ(size_t(0), ring_buffer.guess_size());
  ASSERT_EQ(round_to_power_of_two(capacity), ring_buffer.guess_free_space());
  ASSERT_EQ(size_t(0), msg_count.load());
}

TEST(RingBuffer, MultipleThreads) {
  ASSERT_NO_THROW(test_multiple_threads<false>(23, 237, 1));
}

TEST(RingBuffer, MultipleThreadsMultipleMsgs) {
  ASSERT_NO_THROW(test_multiple_threads<false>(3, 8, 4));
}

TEST(RingBuffer, MultipleThreadsMultipleEntrance) {
  ASSERT_NO_THROW(test_multiple_threads<true>(3, 16, 1));
}

TEST(RingBuffer, MultipleThreadsMultipleMsgsMultipleEntrance) {
  ASSERT_NO_THROW(test_multiple_threads<true>(17, 7, 233));
}

TEST(PerCpuRingBuffer, Allocation) {
  const size_t RING_BUFFER_SIZE = 5;
  PerCpuRingBuffer<int> ring_buffer(RING_BUFFER_SIZE);
  EXPECT_EQ(std::thread::hardware_concurrency(), ring_buffer.get_cpu_count());

  for (size_t i = 0; i < ring_buffer.get_cpu_count(); i++) {
    std::thread([&] {
      EXPECT_EQ(0, set_cpu_affinity(i));
      EXPECT_EQ(i, (get_cached_cpu_of_this_thread()));
      while (!ring_buffer.try_write(i)) {}
    }).join();
  }

  for (size_t i = 0; i < ring_buffer.get_cpu_count(); i++) {
    EXPECT_EQ(size_t(1), ring_buffer.guess_size(i));

    int data;
    EXPECT_TRUE(ring_buffer.try_read(&data, i));
    EXPECT_EQ(i, data);
  }
}

}  // namespace particle

