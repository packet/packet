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
 * @brief IO vector, the ref-counted buffer in packet.
 *
 * @author Soheil Hassas Yeganeh <soheil@cs.toronto.edu>
 * @version 0.1
 */

#ifndef CPP_PACKET_VECTOR_H_
#define CPP_PACKET_VECTOR_H_

#include <cstring>

#include <memory>
#include <vector>

#include "boost/format.hpp"

#include "gtest/gtest.h"

#include "packet/exceptions.h"
#include "packet/internal/packet.h"
#include "packet/internal/vector.h"
#include "packet/packet_fwd.h"

#include "particle/branch.h"
#include "particle/byteordering.h"
#include "particle/type_traits.h"

namespace packet {

class IoVector final {
 public:
  typedef packet::internal::IoVector SharedIoVector;
  typedef std::shared_ptr<SharedIoVector> SharedIoVectorPtr;
  typedef std::shared_ptr<const SharedIoVector> ConstSharedIoVectorPtr;

  ~IoVector() {}

  // Default copy-constructible and move-constructible.
  IoVector(const IoVector&) = default;
  IoVector(IoVector&&) = default;

  // Not move/copy-assignable.
  IoVector& operator=(const IoVector&) = delete;
  IoVector& operator=(IoVector&&) = delete;

  /**
   * @return The allocated size for IO vector. This is always larger than or
   *         equal to the actually consumed number of bytes in the vector.
   */
  size_t size() const noexcept {
    return shared_io_vector->size() - offset;
  }

  template <typename Data, bool is_big_endian = false>
  Data read_data(size_t offset = 0) const {
    return do_read_data<Data, is_big_endian>(offset);
  }

  template <typename Data, bool is_big_endian = false>
  void write_data(const Data& data, size_t offset = 0) {
    do_write_data<Data, is_big_endian>(data, offset);
  }

  template <typename Data, bool is_big_endian = false>
  typename ::std::enable_if<std::is_base_of<Packet, Data>::value,
      std::vector<std::shared_ptr<Data>>>::type  // NOLINT
  read_repeated_data(size_t offset = 0, size_t count = 0, size_t size = 0)
      const {
    std::vector<std::shared_ptr<Data>> result;
    foreach_repeated_data<Data>(offset, count, size,
        [&result](const IoVector& vec, size_t element_size) {
          result.push_back(make_packet<Data>(vec));
        });
    return result;
  }

  // TODO(soheil): Do we really need a shared_ptr here?
  template <typename Data, bool is_big_endian = false>
  typename ::std::enable_if<std::is_integral<Data>::value,
      std::vector<std::shared_ptr<Data>>>::type  // NOLINT
  read_repeated_data(size_t offset = 0, size_t count = 0, size_t size = 0)\
      const {
    std::vector<std::shared_ptr<Data>> result;
    foreach_repeated_data<Data>(offset, count, size,
        [&result](const IoVector& vec, size_t element_size) {
          result.push_back(std::make_shared<Data>(
              vec.read_data<Data, is_big_endian>(0)));
        });
    return result;
  }

  template <typename Data>
  size_t get_repeated_data_size(size_t offset = 0, size_t count = 0,
      size_t size = 0) const {
    size_t data_size = 0;
    foreach_repeated_data<Data>(offset, count, size,
        [&data_size](const IoVector& vec, size_t element_size) {
          data_size += element_size;
        });
    return data_size;
  }

  void consume(size_t size) {
    if (!unlikely(resides_in_buffer(0, size))) {
      // This is not possible, but this makes the implementation more robust.
      throw NotEnoughDataException("Not enough data to move the position.");
    }

    offset += size;
  }

  void expand(size_t delta_size, size_t consumed_size) {
    auto remainder = this->size() - consumed_size;
    if (remainder > delta_size) {
      // We have enough room for the new data.
      return;
    }

    throw std::runtime_error("Cannot really expand unallocated IoVector.");
  }

  void open_gap(size_t offset, size_t gap_size, size_t consumed_size) {
    assert(offset <= consumed_size);
    if (unlikely(gap_size == 0)) {
      return;
    }

    this->expand(gap_size, consumed_size);
    this->memmove(this, offset + gap_size, this, offset,
        consumed_size - offset);
  }

  static void memmove(IoVector* that, size_t to,
      const IoVector* self, size_t from, size_t size) {
    packet::internal::IoVector::memmove(that->shared_io_vector.get(), to,
        self->shared_io_vector.get(), from, size);
  }

  static void memmove(IoVector* that, const IoVector* self, size_t size) {
    memmove(that, that->offset, self, self->offset, size);
  }

 private:
  /**
   * Creates a vector from shared vector.
   * @param shared_vector The shared IO vector.
   * @param offset The offset in the shared IO vector.
   */
  IoVector(SharedIoVectorPtr shared_vector, size_t offset = 0);

  template <typename Data, bool is_big_endian>
  typename ::std::enable_if<std::is_base_of<Packet, Data>::value, Data>::type
  do_read_data(size_t offset) const {
    IoVector new_vec(*this);
    new_vec.consume(offset);
    return *make_packet<Data>(new_vec);
  }

  template <typename Data, bool is_big_endian>
  typename ::std::enable_if<std::is_integral<Data>::value, Data>::type
  do_read_data(size_t offset) const {
    if (unlikely(!resides_in_buffer(offset, sizeof(Data)))) {
      throw NotEnoughDataException("Read exceeds buffer size.");
    }

    const Data* data = (const Data*) get_buf(offset);
    return is_big_endian ? particle::ntohxx(*(data)) : *(data);
  }

  template <typename Data, bool is_big_endian>
  typename ::std::enable_if<particle::is_std_array<Data>::value, Data>::type
  do_read_data(size_t offset) const {
    const size_t no_of_elements = std::tuple_size<Data>::value;
    const size_t element_size = sizeof(typename Data::value_type);
    if (unlikely(!resides_in_buffer(offset, element_size * no_of_elements))) {
      throw NotEnoughDataException("Read exceeds buffer size.");
    }

    Data ret;
    for (size_t i = 0; i < no_of_elements; i++) {
      ret[i] = read_data<typename Data::value_type, is_big_endian>(
          offset + i * element_size);
    }
    return ret;
  }

  template <typename Data, bool is_big_endian>
  typename ::std::enable_if<std::is_base_of<Packet, Data>::value, void>::type
  do_write_data(const Data& data, size_t offset = 0) {
    memmove(this, offset, data.get_io_vector(), 0, data.size());
  }

  template <typename Data, bool is_big_endian>
  typename ::std::enable_if<std::is_integral<Data>::value, void>::type
  do_write_data(const Data& data, size_t offset = 0) {
    if (unlikely(!resides_in_buffer(offset, sizeof(data)))) {
      throw NotEnoughDataException("No space available.");
    }

    auto d = is_big_endian ? particle::ntohxx(data) : data;
    std::memmove(get_buf(offset), &d, sizeof(d));
  }

  template <typename Data, bool is_big_endian>
  typename ::std::enable_if<particle::is_std_array<Data>::value, void>::type
  do_write_data(const Data& data, size_t offset = 0) {
    for (size_t i = 0; i < std::tuple_size<Data>::value; i++) {
      do_write_data(data[i], offset + i * sizeof(typename Data::value_type));
    }
  }

  template <typename Data, typename P>
  void foreach_repeated_data(size_t offset, size_t data_count, size_t data_size,
      P processor) const {
    if (unlikely(data_count == 0 || data_size == 0)) {
      return;
    }

    IoVector new_vec = *this;
    new_vec.consume(offset);

    while (data_count > 0 && data_size > 0) {
      auto element_size = packet::internal::get_data_size<Data>(new_vec);
      assert(element_size != 0);
      if (unlikely(element_size > data_size)) {
        break;
      }

      processor(new_vec, element_size);
      data_count--;
      data_size -= element_size;
      new_vec.consume(element_size, false);
    }
  }

  bool resides_in_buffer(size_t offset, size_t size) const {
    // TODO(soheil): Is this valnurable to overflows?
    return shared_io_vector->size() >= this->offset + offset + size;
  }

  SharedIoVectorPtr get_shared_vector() { return shared_io_vector; }
  ConstSharedIoVectorPtr get_shared_vector() const { return shared_io_vector; }

  char* get_buf(size_t offset = 0) {
    return shared_io_vector->get_buf(this->offset + offset);
  }

  const char* get_buf(size_t offset = 0) const {
    return shared_io_vector->get_buf(this->offset + offset);
  }

  SharedIoVectorPtr shared_io_vector;
  size_t offset;

  template <typename Packet>
  friend class Channel;
  friend class Packet;

  friend IoVector make_io_vector(const SharedIoVectorPtr&);
  friend IoVector make_iov(size_t, uint8_t);
  friend IoVector make_packet_iov(size_t);

  FRIEND_TEST(IoVectorTest, BoundChecks);
  FRIEND_TEST(IoVectorTest, Consume);
  FRIEND_TEST(IoVectorTest, ReadData);
};

inline IoVector make_io_vector(
    const std::shared_ptr<packet::internal::IoVector>& shared_io_vector) {
  return IoVector(shared_io_vector);
}

inline IoVector make_io_vector(size_t size) {
  return make_io_vector(packet::internal::make_shared_io_vector(size));
}

}  // namespace packet

#endif  // CPP_PACKET_VECTOR_H_
