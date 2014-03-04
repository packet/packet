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
 * @brief Internal implementation of a memory buffer.
 *
 * @author Soheil Hassas Yeganeh <soheil@cs.toronto.edu>
 * @version 0.1
 */

#ifndef CPP_PACKET_INTERNAL_VECTOR_H_
#define CPP_PACKET_INTERNAL_VECTOR_H_

#include <cstdlib>
#include <cassert>

#include <atomic>
#include <memory>

#include "boost/intrusive_ptr.hpp"

#include "gtest/gtest.h"

#include "particle/branch.h"

#include "packet/internal/packet_fwd.h"

namespace packet {
namespace internal {

/**
 * A reference counted structure that stores the memory for IO vectors.
 */
class IoVector final {
 public:
  typedef uint64_t MetaData;
  typedef size_t RefCount;

  // Not copyable nor movable.
  IoVector(const IoVector&) = delete;
  IoVector(IoVector&&) = delete;

  IoVector& operator=(const IoVector&) = delete;
  IoVector& operator=(IoVector&&) = delete;

  /** Returns the io vectors. */
  char* get_buf(size_t offset = 0) {
    assert(offset < size());
    return buf + offset;
  }

  const char* get_buf(size_t offset = 0) const {
    assert(offset < size());
    return buf + offset;
  }

  /** IO vector's size. */
  size_t size() const { return buf_size; }

  /** Returns the meta-data. */
  MetaData get_metadata() const {
    return metadata.load(std::memory_order_acquire);
  }

  /** Sets the meta-data. */
  void set_metadata(MetaData metadata) {
    this->metadata.store(metadata, std::memory_order_release);
  }

  /** Adds to the reference count. */
  RefCount add_ref(RefCount diff = 1,
                   std::memory_order order = std::memory_order_seq_cst) {
    return ref_count.fetch_add(diff, order) + diff;
  }

  /** Subtracts from the reference count. */
  RefCount release(RefCount diff = 1,
                   std::memory_order order = std::memory_order_seq_cst) {
    return ref_count.fetch_sub(diff, order) - diff;
  }

  static void memmove(IoVector* that, size_t to, const IoVector* self,
                      size_t from, size_t size);

  static void memmove(char* that, size_t to, const IoVector* self, size_t from,
                      size_t size);

  static void memmove(IoVector* that, size_t to, const char* self, size_t from,
                      size_t size);

 private:
  IoVector(char* buf, size_t size)
      : buf(buf), buf_size(size), metadata(0), ref_count(0) {
    assert(buf != nullptr);
  }

  char* const buf;
  const size_t buf_size;

  /**
   * Meta-data shared for this buffer. This usually stores an identifier for
   * the source channel, but the user can also store other information.
   */
  std::atomic<MetaData> metadata;

  /** This is used by boost::intrusive_ptr. */
  std::atomic<RefCount> ref_count;

  friend void intrusive_ptr_add_ref(IoVector* vector);
  friend void intrusive_ptr_release(IoVector* vector);
  friend boost::intrusive_ptr<IoVector> make_shared_io_vector(size_t size);

  FRIEND_TEST(IoVector, ThreadSafety);
};

inline void intrusive_ptr_add_ref(packet::internal::IoVector* vector) {
  vector->add_ref(1, std::memory_order_relaxed);
}

inline void intrusive_ptr_release(packet::internal::IoVector* vector) {
  if (vector->release(1, std::memory_order_release) == 0) {
    std::atomic_thread_fence(std::memory_order_acquire);
    free(static_cast<void*>(vector));
  }
}

inline boost::intrusive_ptr<IoVector> make_shared_io_vector(size_t size) {
  auto chunk = static_cast<char*>(calloc(sizeof(IoVector) + size, 1));
  if (unlikely(chunk == nullptr)) {
    return boost::intrusive_ptr<IoVector>();
  }

  return boost::intrusive_ptr<IoVector>(
      new (chunk) IoVector(chunk + sizeof(IoVector), size));  // NOLINT
}

}  // namespace internal
}  // namespace packet

#endif  // CPP_PACKET_INTERNAL_VECTOR_H_

