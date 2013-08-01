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
 * @brief Unit test for type names.
 *
 * @author Soheil Hassas Yeganeh <soheil@cs.toronto.edu>
 * @version 0.1
 */

#include <memory>
#include <string>
#include <vector>

#include "particle/typename.h"
#include "gtest/gtest.h"

namespace particle {

TEST(TypeNameTest, IntegralNames) {
  EXPECT_EQ("@b", demangle_type<bool>());
  EXPECT_EQ("@c", demangle_type<char>());
  EXPECT_EQ("@h", demangle_type<short>());  // NOLINT
  EXPECT_EQ("@i", demangle_type<int>());
  EXPECT_EQ("@l", demangle_type<long>());  // NOLINT
  EXPECT_EQ("@l", demangle_type<long int>());  // NOLINT

  EXPECT_EQ("@u", demangle_type<unsigned int>());
  EXPECT_EQ("@cu", demangle_type<std::uint8_t>());

  EXPECT_EQ("@i", demangle_type<const int>());
  EXPECT_EQ("@i", demangle_type<const int>(false));
}

TEST(TypeNameTest, TemplateClasses) {
  EXPECT_EQ("std::shared_ptr<@s>",
      demangle_type<const std::shared_ptr<const std::string>>());
  EXPECT_EQ("std::shared_ptr<@s const>",
      demangle_type<const std::shared_ptr<const std::string>>(false));
  EXPECT_EQ("std::shared_ptr<@s const>",
      demangle_type<const std::shared_ptr<std::string const>>(false));

  EXPECT_EQ(demangle_type<std::shared_ptr<std::string>>(),
      demangle_type<std::shared_ptr<const std::string>>());
  EXPECT_NE(demangle_type<std::shared_ptr<int>>(),
      demangle_type<std::shared_ptr<const int>>(false));
}

TEST(TypeNameTest, Pairs) {
  typedef std::pair<int, long> ThePair;  // NOLINT
  EXPECT_EQ("<@i, @l>", demangle_type<ThePair>());
}

class Base {
 public:
  virtual ~Base() {}
};

class Derived : public Base {
};

TEST(TypeNameTest, PolymorphicTypeName) {
  Base* base = new Derived();
  EXPECT_EQ("particle::Derived", type_name(*base));
  delete(base);
}

}  // namespace particle

