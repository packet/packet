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
 * @brief Common utilities for managed pointers.
 *
 * @author Soheil Hassas Yeganeh <soheil@cs.toronto.edu>
 * @version 0.1
 */


#ifndef CPP_PARTICLE_MEMORY_H_
#define CPP_PARTICLE_MEMORY_H_

#include <memory>

namespace particle {

/**
 * Represents objects that can be created only as shared_ptr's. Note that
 * constructors must be non-public.
 *
 * Usage:
 *    class Klass : public SharedOnly<Klass> {
 *      ...
 *     protected:
 *      Klass() = default;
 *      ... other constructors ...
 *      FRIEND_SHARED_ONLY(Klass);
 *    };
 *
 *    auto klass = Klass::make_shared<Klass>
 */
template <typename T>
class SharedOnly : public std::enable_shared_from_this<T> {
 public:
  std::shared_ptr<T> get_shared() {
    return this->shared_from_this();
  }

  /**
   * Creates a shared pointer holding a reference.
   */
  template <typename D = T, typename... Args>
  static std::shared_ptr<D> make_shared(Args... args) {
    static_assert(std::is_base_of<T, D>::value, "D must be derived from T.");
    return std::shared_ptr<D>(new D(args...));
  }
};

#define FRIEND_SHARED_ONLY(T) friend class particle::SharedOnly<T>

}  // namespace particle

#endif  // CPP_PARTICLE_MEMORY_H_

