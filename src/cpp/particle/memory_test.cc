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
 * @brief Unit test for managed pointers.
 *
 * @author Soheil Hassas Yeganeh <soheil@cs.toronto.edu>
 * @version 0.1
 */

#include <memory>
#include <string>
#include <vector>

#include "particle/memory.h"
#include "gtest/gtest.h"

namespace particle {

class MySharedOnlyBase : public SharedOnly<MySharedOnlyBase> {
 public:
  virtual ~MySharedOnlyBase() {}

 protected:
  MySharedOnlyBase() = default;

  FRIEND_SHARED_ONLY(MySharedOnlyBase);
};

class MySharedOnlyDerived : public MySharedOnlyBase {
 private:
  MySharedOnlyDerived() = default;

  FRIEND_SHARED_ONLY(MySharedOnlyBase);
};

TEST(MemoryTest, SharedOnly) {
  auto main_shared = MySharedOnlyBase::make_shared();
  EXPECT_NE(nullptr, main_shared);
  auto copy_shared = main_shared->get_shared();
  EXPECT_EQ(main_shared, copy_shared);
  EXPECT_EQ(2, main_shared.use_count());
}

TEST(MemoryTest, SharedOnlyInheritance) {
  auto main_shared = MySharedOnlyDerived::make_shared<MySharedOnlyDerived>();
  EXPECT_NE(nullptr, main_shared);
  auto copy_shared =
    std::dynamic_pointer_cast<MySharedOnlyDerived>(main_shared);
  EXPECT_NE(nullptr, copy_shared);
  EXPECT_EQ(main_shared, copy_shared);
  EXPECT_EQ(2, main_shared.use_count());
}

}  // namespace particle

