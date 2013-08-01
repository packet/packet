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
 * @brief Unit test bit hacks.
 *
 * @author Soheil Hassas Yeganeh <soheil@cs.toronto.edu>
 * @version 0.1
 */

#include <cstdint>

#include "particle/bithacks.h"
#include "gtest/gtest.h"

namespace particle {

TEST(BitHacksTest, RoundToClosestPowerOfTwo) {
  EXPECT_EQ(uint8_t(0x80), round_to_power_of_two(uint8_t(0x7E)));
  EXPECT_EQ(uint8_t(0x04), round_to_power_of_two(uint8_t(0x03)));
  EXPECT_EQ(uint8_t(0x02), round_to_power_of_two(uint8_t(0x02)));
  EXPECT_EQ(uint16_t(0x8000), round_to_power_of_two(uint16_t(0x7FFF)));
  EXPECT_EQ(uint32_t(1) << 31, round_to_power_of_two((uint32_t(1) << 31) - 1));
  EXPECT_EQ(uint64_t(8), round_to_power_of_two(uint64_t(7)));
  EXPECT_EQ(uint64_t(0x1000000000000000),
      round_to_power_of_two(uint64_t(0x0FFFFFFFFFFFFFFF)));
}

}  // namespace particle

