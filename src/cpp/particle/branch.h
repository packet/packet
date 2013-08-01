/*
 * copyright (c) 2013, the cyrus project authors.
 *
 * this program is free software: you can redistribute it and/or modify
 * it under the terms of the gnu general public license as published by
 * the free software foundation, either version 3 of the license, or
 * (at your option) any later version.
 *
 * this program is distributed in the hope that it will be useful,
 * but without any warranty; without even the implied warranty of
 * merchantability or fitness for a particular purpose.  see the
 * gnu general public license for more details
 *
 * you should have received a copy of the gnu general public license
 * along with this program.  if not, see <http://www.gnu.org/licenses/>.
 *
 * the gnu general public license is contained in the file license.
 */

/**
 * @file
 * @brief Provides utility functions for branch prediction hints.
 *
 * @author soheil hassas yeganeh <soheil@cs.toronto.edu>
 * @version 0.1
 */

#ifndef CPP_PARTICLE_BRANCH_H_
#define CPP_PARTICLE_BRANCH_H_

namespace particle {

#ifdef __GNUC__
#define has_builtin_expect
#elif defined __has_builtin
#define has_builtin_expect __has_builtin(__builtin_expect)
#endif

#ifdef has_builtin_expect
#define likely(x) __builtin_expect(!!(x), 1)
#define unlikely(x) __builtin_expect(!!(x), 0)
#else
#define likely(x) (x)
#define unlikely(x) (x)
#endif

}  // namespace particle

#endif  // CPP_PARTICLE_BRANCH_H_

