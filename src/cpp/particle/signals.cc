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

#include <pthread.h>

#include <atomic>
#include <csignal>
#include <functional>
#include <thread>
#include <vector>
#include <unordered_map>

#include "particle/branch.h"
#include "particle/signals.h"

namespace particle {

using std::function;
using std::initializer_list;
using std::thread;
using std::vector;
using std::unordered_map;

void clean_up_callback(int signal);

/**
 * Manages all signals in the controller. Note: It's a singleton.
 * @see get_singal_master()
 */
class SignalMaster final {
 public:
  /**
   * Default termaination signals.
   */
  static initializer_list<int> SIGNALS;
  /**
   * Registers a new clean up handler.
   * @param cleanup_handler The cleanup handler.
   */
  HandlerId add_cleanup_handler(
      const function<void()>& cleanup_handler) {
    static std::atomic<HandlerId> start_id(0);
    start_id++;
    cleanup_handlers[start_id] = cleanup_handler;
    return start_id;
  }
  /**
   * Removes the cleanup handler.
   * @param id The id of the cleanup handler.
   */
  void remove_cleanup_handler(HandlerId id) {
    cleanup_handlers.erase(id);
  }
  /**
   * Calls the cleanup handlers. Note: It will block if any of the handlers
   * block.
   */
  void cleanup() {
    auto cleanup_handlers = this->cleanup_handlers;  // Safer to copy.
    for (auto handler : cleanup_handlers) {
      handler.second();
    }
  }
  /**
   * @return Whether the calling thread is the main thread.
   */
  bool is_main_thread() {
    return std::this_thread::get_id() == main_thread_id;
  }

 private:
  SignalMaster() : main_thread_id(std::this_thread::get_id()) {
    register_event_handlers(SIGNALS);
  }

  void register_event_handlers(initializer_list<int> signals) {
    for (int signal_no : signals) {
      signal(signal_no, clean_up_callback);
    }
  }

  thread::id main_thread_id;
  unordered_map<HandlerId, function<void()>> cleanup_handlers;

  friend SignalMaster* get_signal_master();
};

initializer_list<int> SignalMaster::SIGNALS = {SIGINT, SIGTERM};

SignalMaster* get_signal_master() {
  static SignalMaster signal_master;
  return &signal_master;
}

HandlerId register_cleanup_handler(::std::function<void()> cleanup_handler) {
  return get_signal_master()->add_cleanup_handler(cleanup_handler);
}

void remove_cleanup_handler(HandlerId id) {
  get_signal_master()->remove_cleanup_handler(id);
}

void clean_up_callback(int signal) {
  get_signal_master()->cleanup();
}

CleanupGaurd::CleanupGaurd(std::function<void()> cleanup_handler)
    : cleanup_handler_id(-1) {
  if (cleanup_handler) {
    cleanup_handler_id = register_cleanup_handler(cleanup_handler);
  }
}

CleanupGaurd::~CleanupGaurd() {
  if (unlikely(cleanup_handler_id == -1)) {
    return;
  }

  remove_cleanup_handler(cleanup_handler_id);
}

/**
 * Initializes the current thread for signals. It basically blocks termination
 * signals on threads.
 */
void init_thread() {
  // Ignore the main thread.
  if (get_signal_master()->is_main_thread()) {
    return;
  }

  sigset_t signal_set;
  sigemptyset(&signal_set);
  for (int signal_no : SignalMaster::SIGNALS) {
    sigaddset(&signal_set, signal_no);
  }

  pthread_sigmask(SIG_BLOCK, &signal_set, nullptr);
}

}  // namespace particle

