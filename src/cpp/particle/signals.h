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
 * @brief Common utilities for signal handling.
 *
 * @author Soheil Hassas Yeganeh <soheil@cs.toronto.edu>
 * @version 0.1
 */

#ifndef CPP_PARTICLE_SIGNALS_H_
#define CPP_PARTICLE_SIGNALS_H_

#include <functional>

namespace particle {

typedef int HandlerId;

/** A RIAA class for clean up handler upon program termination. */
class CleanupGaurd final {
 public:
  CleanupGaurd(std::function<void()> cleanup_handler);

  ~CleanupGaurd();

 private:
  HandlerId cleanup_handler_id;
};

/**
 * Initializes the current thread for signals. It basically blocks termination
 * signals on threads.
 */
void init_thread();

}  // namespace particle

#endif  // CPP_PARTICLE_SIGNALS_H_

