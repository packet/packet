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
 * @brief Utilities to get cpu information.
 *
 * @author Soheil Hassas Yeganeh <soheil@cs.toronto.edu>
 * @version 0.1
 */

#ifndef CPP_PARTICLE_CPU_H_
#define CPP_PARTICLE_CPU_H_

#ifdef __linux__
#include <sched.h>
#else
#error Cannot use getcpu for your platform.
#endif

namespace particle {

typedef int32_t CpuId;

/**
 * @return The cpu id for the current execution thread.
 */
inline CpuId get_cpu() {
  return CpuId(sched_getcpu());
}

/** Sets the cpu affinity of the given thread. */
int set_cpu_affinity(const std::thread& thread, CpuId cpu_id);

/** Set the cpu affinity of the current thread. */
int set_cpu_affinity(CpuId cpu_id);

/** Returns the cached cpu id for this thread. */
CpuId get_cached_cpu_of_this_thread();

}  // namespace particle

#endif  // CPP_PARTICLE_CPU_H_

