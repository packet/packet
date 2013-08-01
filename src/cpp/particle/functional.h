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
 * @brief Common utilities for functions, functors, and lambdas.
 *
 * @author Soheil Hassas Yeganeh <soheil@cs.toronto.edu>
 * @version 0.1
 */


#ifndef CPP_PARTICLE_FUNCTIONAL_H_
#define CPP_PARTICLE_FUNCTIONAL_H_

#include <atomic>

namespace particle {

template <typename Function>
bool can_call() {
  static ::std::atomic<bool> called(false);
  return !called.exchange(true);
}

template <typename Function>
void call_once(Function func) {
  if (can_call<Function>()) {
    func();
  }
}

}  // namespace particle

#endif  // CPP_PARTICLE_FUNCTIONAL_H_

