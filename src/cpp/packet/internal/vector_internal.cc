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
 * @brief Internal implementation of a memory buffer.
 *
 * @author Soheil Hassas Yeganeh <soheil@cs.toronto.edu>
 * @version 0.1
 */

#include <cstring>

#include <algorithm>

#include "particle/branch.h"

#include "packet/internal/vector.h"

namespace packet {
namespace internal {

void IoVector::memmove(IoVector* that, size_t to,
    const IoVector* self, size_t from, size_t size) {
  if (unlikely(size == 0)) {
    return;
  }

  if (unlikely(from >= self->size()) || unlikely(to >= that->size())) {
    return;
  }

  auto size_to_copy = std::min({ size, self->size() - from, that->size() - to});
  std::memmove(that->get_buf(to), self->get_buf(from), size_to_copy);
}

}  // namespace internal
}  // namespace packet

