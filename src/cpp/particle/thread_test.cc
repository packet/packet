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
 * @brief Unit test for threads.
 *
 * @author Soheil Hassas Yeganeh <soheil@cs.toronto.edu>
 * @version 0.1
 */

#include <memory>
#include <string>
#include <vector>

#include "gtest/gtest.h"

#include "particle/thread.h"

namespace particle {

class DummyTag;

TEST(StaticThreadLocal, SetValue) {
  EXPECT_EQ(0, (get_thread_local<int, DummyTag>()));

  int i = 0xDEADBEEF;
  set_thread_local<int, DummyTag>(i);
  EXPECT_EQ(i, (get_thread_local<int, DummyTag>()));

  auto th = std::thread([]() {
    EXPECT_EQ(0, (get_thread_local<int, DummyTag>()));
  });
  th.join();
}

}  // namespace particle

