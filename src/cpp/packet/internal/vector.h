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

  /**
   * @param channel The packet channel that this IO vector is attached to.
   * @param size Buffer size. Must be more than 0.
   * Note: Do not use this construtor directly. Use make_shared_io_vector
   *       instead.
   */
  explicit IoVector(size_t size)
      : IoVector(static_cast<char *>(malloc(size)), size) {}

  IoVector(char* buf, size_t size)
      : buf(buf), buf_size(size), metadata(0), ref_count(0) {
    assert(buf != nullptr);
  }

  // Not default copyable.
  IoVector(const IoVector&) = delete;
  IoVector& operator=(const IoVector&) = delete;

  // Default movable.
  IoVector(IoVector&&) = default;
  IoVector& operator=(IoVector&&) = default;

  ~IoVector() {
    if (unlikely(buf == nullptr)) {
      return;
    }
    free(buf);
  }

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
  MetaData get_metadata() const { return metadata.load(); }

  /** Sets the meta-data. */
  void set_metadata(MetaData metadata) { this->metadata.store(metadata); }

  /** Adds to the reference count. */
  RefCount add_ref(RefCount diff = 1) {
    return ref_count.fetch_add(diff) + diff;
  }

  /** Subtracts from the reference count. */
  RefCount release(RefCount diff = 1) {
    return ref_count.fetch_sub(diff) - diff;
  }

  static void memmove(IoVector* that, size_t to, const IoVector* self,
                      size_t from, size_t size);

  static void memmove(char* that, size_t to, const IoVector* self, size_t from,
                      size_t size);

  static void memmove(IoVector* that, size_t to, const char* self, size_t from,
                      size_t size);

 private:
  char* buf;
  size_t buf_size;

  /**
   * Meta-data shared for this buffer. This usually stores an identifier for
   * the source channel, but the user can also store other information.
   */
  std::atomic<MetaData> metadata;

  /** This is used by boost::intrusive_ptr. */
  std::atomic<RefCount> ref_count;

  friend void intrusive_ptr_add_ref(IoVector* vector);
  friend void intrusive_ptr_release(IoVector* vector);

  FRIEND_TEST(IoVector, ThreadSafety);
};

inline void intrusive_ptr_add_ref(packet::internal::IoVector* vector) {
  vector->add_ref();
}

inline void intrusive_ptr_release(packet::internal::IoVector* vector) {
  if (vector->release() == 0) {
    delete(vector);
  }
}

template <typename... Args>
boost::intrusive_ptr<IoVector> make_shared_io_vector(Args... args) {
  return boost::intrusive_ptr<IoVector>(new IoVector(args...));
}

}  // namespace internal
}  // namespace packet

#endif  // CPP_PACKET_INTERNAL_VECTOR_H_

