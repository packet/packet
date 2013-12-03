/*
 * Copyright (C) 2012-2013, The Particle project authors.
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
 * @brief Common utilities for threads in Particle.
 *
 * @author Soheil Hassas Yeganeh <soheil@cs.toronto.edu>
 * @version 0.1
 */

#ifndef CPP_PARTICLE_THREAD_H_
#define CPP_PARTICLE_THREAD_H_

#include <thread>

#include "particle/signals.h"

namespace particle {

/**
 * Creates a thread that runs the function, and also registers the cleanup
 * function.
 * @param func
 * @param cleanup_handler
 * @return
 */
template <typename Function>
std::function<void()> make_particle_thread(Function func) {
  return [func]() mutable {  // NOLINT
    init_thread();
    func();
  };
}

/**
 * Static per thread storage. This is a much simpler version of
 * folly::StaticMeta with no special functionality.
 */
template <typename Value, typename Tag>
class StaticThreadLocal {
 public:
  static Value get() {
    return StaticThreadLocal::value;
  }

  static void set(Value value) {
    StaticThreadLocal::value = value;
  }

 private:
  static __thread Value value;
};

template <typename Value, typename Tag>
__thread Value StaticThreadLocal<Value, Tag>::value {};  // NOLINT

template <typename Value, typename Tag>
Value get_thread_local() {
  return StaticThreadLocal<Value, Tag>::get();
}

template <typename Value, typename Tag>
void set_thread_local(Value value) {
  StaticThreadLocal<Value, Tag>::set(value);
}

}  // namespace particle

#endif  // CPP_PARTICLE_THREAD_H_

