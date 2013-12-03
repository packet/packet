/*
 * Copyright (C) 2013, The Cyrus project authors.
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
 * @brief Utility classes for dynamic arrays.
 *
 * @author Soheil Hassas Yeganeh <soheil@cs.toronto.edu>
 * @version 0.1
 */


#ifndef CPP_PARTICLE_ARRAY_H_
#define CPP_PARTICLE_ARRAY_H_

#include <cstdlib>

#include <algorithm>
#include <utility>

namespace particle {

/**
 * This is dynamic array implementation for noncopyable, nonmovable classes. It
 * does not provide iterators. The container itself is non-copyable but is
 * movable.
 */
template <typename Element>
class DynamicArray {
 public:
  typedef Element* ElementArray;
  typedef Element* ElementPtr;
  typedef Element& ElementRef;
  typedef size_t SizeType;

  ~DynamicArray() {
    if (elements == nullptr) {
      return;
    }

    for (SizeType i = 0; i < array_size; i++) {
      elements[i].~Element();
    }

    free(elements);
  }

  DynamicArray(const DynamicArray&) = delete;

  DynamicArray(DynamicArray&& that) : elements(nullptr), array_size(0) {
    std::swap(elements, that.elements);
    std::swap(array_size, that.array_size);
  };

  DynamicArray& operator=(const DynamicArray&) = delete;

  DynamicArray& operator=(DynamicArray&& that) {
    this->elements = that.elements;
    this->array_size = that.array_size;

    that.elements = nullptr;
    that.array_size = 0;

    return *this;
  };

  /** Returns the index'th element of the array. */
  ElementPtr get(SizeType index) const {
    return &elements[index];
  }

  /** Returns the index'th element of the array. */
  ElementRef operator[](SizeType index) const {
    return elements[index];
  }

  /** Returns the size of this array. It's O(1). */
  SizeType size() const {
    return array_size;
  }

  template <typename F>
  void for_each(F f) {
    for (SizeType i = 0; i < array_size; i++) {
      f(elements[i]);
    }
  }

 private:
  explicit DynamicArray(const SizeType size)
      : elements(
            static_cast<ElementArray>(std::malloc(sizeof(Element) * size))),
        array_size(size) {}

  template <typename... Args>
  void init(SizeType index, Args... args) {
    new (&elements[index]) Element(std::forward<Args>(args)...);  // NOLINT
  }

  ElementArray elements;
  SizeType array_size;

  template <typename E, typename... Args>
  friend DynamicArray<E> make_array(size_t size, Args... args);
};

template <typename Element, typename... Args>
DynamicArray<Element> make_array(size_t size,
                                 Args... args) {
  DynamicArray<Element> array(size);
  for (size_t i = 0; i < size; i++) {
    array.init(i, args...);
  }
  return array;
}

}  // namespace particle

#endif  // CPP_PARTICLE_ARRAY_H_

