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
 * @brief Thread-safe, lockless ring buffer.
 *
 * @author Soheil Hassas Yeganeh <soheil@cs.toronto.edu>
 * @version 0.1
 */

#ifndef CPP_PARTICLE_RINGBUFFER_H_
#define CPP_PARTICLE_RINGBUFFER_H_

#include <boost/optional.hpp>

#include <atomic>
#include <cassert>
#include <cstdlib>
#include <sstream>

#include <list>
#include <memory>
#include <mutex>

#include "particle/bithacks.h"

namespace particle {

/**
 * A lockless, multiple-producer multiple-consumer ring buffer. Provably correct
 * implementation for up to 2^64 (and 2^32 on 32-bit systems) simultanous reads
 * and writes.
 * This code is based on folly::ProducerConsumerQueue:
 * https://github.com/facebook/folly/blob/master/folly/ProducerConsumerQueue.h.
 *
 * Limitations:
 * - It does not support dynamic sizing.
 */
template <typename T, bool allow_multiple_entrance = false>
class RingBuffer final {
 public:
  /**
   * @param capacity The capacity of the ring buffer. Capacity must be larger
   *     than 1.
   * Note: The capacity will be rounded to closest power of two.
   * Note: The buffer can hold at most (capacity - 1) elements.
   */
  explicit RingBuffer(size_t capacity)
      // FIXME: Read and document these again!
      : lower_free_index(0),
        upper_free_index(0),
        lower_full_index(0),
        upper_full_index(0),
        buffer_capacity(round_to_power_of_two(capacity)),
        buffer(static_cast<T*>(std::malloc(sizeof(T) * buffer_capacity))) {
    assert(buffer_capacity >= 2);
    if (!buffer) {
      throw std::bad_alloc();
    }
  }

  ~RingBuffer() {
    // We need to destruct anything that may still exist in our queue.
    // (No real synchronization needed at destructor time: only one
    // thread can be doing this.)
    if (!std::has_trivial_destructor<T>::value) {
      while (try_read()) {}
    }

    std::free(buffer);
  }

  /**
   * @param record The record to write. (The record will be moved into the
   *     buffer).
   * @return Whether the write was succesful. Note: It may spuriously fail.
   */
  bool try_write(const T& record) {
    size_t current_free_index = lower_free_index.load();
    size_t next_free_index = 0;

    do {
      // If there is another writer with an onging write.
      if (!allow_multiple_entrance &&
          !index_equal(upper_full_index.load(), current_free_index)) {
        return false;
      }

      // TOOD(soheil): Can we use relaxed memory order here?
      next_free_index = current_free_index + 1;

      // If the buffer is full.
      if (index_equal(upper_free_index.load(), next_free_index)) {
        return false;
      }
    } while (!lower_free_index.compare_exchange_weak(current_free_index,
          next_free_index));


    new (&buffer[masked(next_free_index)]) T(record);  // NOLINT

    // Loops until all prior writes are finished.
    size_t current_free_index_copy;
    do {
      current_free_index_copy = current_free_index;
    } while (!upper_full_index.compare_exchange_weak(current_free_index_copy,
        next_free_index));

    return true;
  }

  /**
   * Tries to read a record from the buffer.
   * @param record Where the result of read is moved to.
   * @return Whether read is successful. Note: It may spuriously fail.
   */
  bool try_read(T* record = nullptr) {
    size_t current_full_index = lower_full_index.load();
    size_t next_full_index = 0;

    do {
      // If there is some reader, with an ongoing read.
      if (!allow_multiple_entrance &&
          !index_equal(upper_free_index.load(), current_full_index)) {
        return false;
      }

      // Buffer is empty.
      if (index_equal(upper_full_index.load(), current_full_index)) {
        return false;
      }

      next_full_index = current_full_index + 1;
    } while (!lower_full_index.compare_exchange_weak(
        current_full_index, next_full_index));

    if (record != nullptr) {
      *record = std::move(buffer[masked(next_full_index)]);
    }

    buffer[masked(next_full_index)].~T();

    // Wait until all prior reads are finished.
    size_t current_full_index_copy;
    do {
      current_full_index_copy = current_full_index;
    } while (!upper_free_index.compare_exchange_weak(
        current_full_index_copy, next_full_index));

    return true;
  }

  size_t guess_size() const {
    return capacity() - guess_free_space();
  }

  size_t guess_free_space() const {
    return circular_diff(lower_free_index.load(std::memory_order_relaxed),
        upper_free_index.load(std::memory_order_relaxed));
  }

  size_t capacity() const {
    return buffer_capacity;
  }

 private:
  /**
   * Measures the circular difference between two indexes.
   * Note: If the second param is larger than the first one, it returns the
   *       simple difference, otherwise the circular difference.
   */
  size_t circular_diff(size_t first, size_t second) const {
    return second > first ? masked(second) - masked(first) :
        capacity() + masked(second) - masked(first);
  }

  bool index_equal(size_t rhs, size_t lhs) const {
    return masked(rhs) == masked(lhs);
  }

  size_t masked(size_t index) const {
    return (buffer_capacity - 1) & index;
  }

  // Invariant: The indices, when masked, have the following circular
  //            relationship:
  //            upper_free_index <= lower_full_index <= upper_full_index <=
  //            lower_free_index
  // Writable area is (lower_free_index, upper_free_index).
  // Readable area is (lower_full_index, upper_full_index].
  // Currently being read area is (upper_free_index, lower_full_index].
  // Currently being written area is (upper_full_index, lower_free_index].

  /**
   * The index pointing to the element right before the first free element,
   * i.e., the element that can be reserved for a write.
   */
  std::atomic<size_t> lower_free_index;
  /** Index pointing to the element right after the last free element. */
  std::atomic<size_t> upper_free_index;
  /** Index pointing to the element right before the First unread element. */
  std::atomic<size_t> lower_full_index;
  /** Index of the last unread element. */
  std::atomic<size_t> upper_full_index;

  /** The maximum capacity of the buffer. */
  const size_t buffer_capacity;

  /** The container that stores buffer elements. */
  T* const buffer;
};

}  // namespace particle

#endif  // CPP_PARTICLE_RINGBUFFER_H_

