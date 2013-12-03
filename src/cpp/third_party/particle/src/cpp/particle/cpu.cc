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

#include <algorithm>
#include <thread>

#include "particle/branch.h"
#include "particle/cpu.h"
#include "particle/thread.h"

namespace particle {

static int set_cpu_affinity(pthread_t handle, CpuId cpu_id) {
  if (cpu_id >= CpuId(std::thread::hardware_concurrency())) {
    return EINVAL;
  }

  cpu_set_t cpuset;
  CPU_ZERO(&cpuset);
  CPU_SET(cpu_id, &cpuset);

  return pthread_setaffinity_np(handle, sizeof(cpu_set_t), &cpuset);
}

int set_cpu_affinity(CpuId cpu_id) {
  return set_cpu_affinity(pthread_self(), cpu_id);
}

int set_cpu_affinity(std::thread* thread, CpuId cpu_id) {
  return set_cpu_affinity(thread->native_handle(), cpu_id);
}

CpuId get_cached_cpu_of_this_thread() {
  class CachedCpuId;

  // We store 1-based cpu ids and use 0 as a sign that the thread local
  // variable is not initialized.
  auto cpu_id = get_thread_local<CpuId, CachedCpuId>();
  if (likely(cpu_id != 0)) {
    return cpu_id - 1;
  }

  // Enforce the cpu_id to be in [0, buffers.size()).
  cpu_id = std::min(std::thread::hardware_concurrency(),
                    unsigned(std::max(0, get_cpu())));
  set_thread_local<CpuId, CachedCpuId>(cpu_id + 1);
  return cpu_id;
}

}  // namespace particle

