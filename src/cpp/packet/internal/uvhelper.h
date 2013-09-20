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
 * @brief Helper classes for libuv.
 *
 * @author Soheil Hassas Yeganeh <soheil@cs.toronto.edu>
 * @version 0.1
 */

#ifndef CPP_PACKET_INTERNAL_UVHELPER_H_
#define CPP_PACKET_INTERNAL_UVHELPER_H_

#include <sys/socket.h>

#include "third_party/libuv/include/uv.h"
#include "particle/memory.h"

#include "packet/internal/packet_fwd.h"

namespace packet {
namespace internal {

/**
 * Abstracts away common functionalities required for a uv loop.
 * Note: Should not be used polymorphically.
 */
class UvLoop {
 public:
  UvLoop() : loop(uv_loop_new()) {}

 protected:
  /** Starts the loop. */
  int start_loop() noexcept {
    return uv_run(loop, UV_RUN_DEFAULT);
  }

  /**
   * Stops the loop.
   * Note: Should be only called inside callbacks for thread saftey reasons.
   */
  void stop_loop() noexcept {
    return uv_stop(loop);
  }

  /** Must be called on destructor of inherited classes. */
  void delete_loop() noexcept {
    // Calls all close handlers.
    // TODO(soheil): submit a patch for this to libuv.
    uv_run(loop, UV_RUN_NOWAIT);

    uv_loop_delete(loop);
  }

  uv_loop_t* loop;
};

}  // namespace internal
}  // namespace packet

#endif  // CPP_PACKET_INTERNAL_UVHELPER_H_
