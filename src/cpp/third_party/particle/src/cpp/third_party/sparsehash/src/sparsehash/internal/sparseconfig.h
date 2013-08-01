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
 * @brief Platform specific header files for sparsemap.
 *
 * @author Soheil Hassas Yeganeh <soheil@cs.toronto.edu>
 */

// Add your platform specific sparseconfig.h below.

#if defined(__APPLE__)
#include "sparsehash/internal/mac/sparseconfig.h"
#elif defined(__linux__)
#include "sparsehash/internal/linux/sparseconfig.h"
#else
#error generate sparseconfig.h for your platform
#endif

