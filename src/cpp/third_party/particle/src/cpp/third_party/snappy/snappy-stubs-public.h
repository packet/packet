/*
 * Copyright (C) 2013 The Chromium Authors. All rights reserved.
 * Copyright (C) 2014, The Particle project authors.
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
 * @brief Snappy config header file for building the library without using
 *        gnu auto tools.
 */

// For adding a new platform, you need to configure and make the project. Then
// add the generated header files to the platform sepcific folder.

#ifndef CPP_THIRD_PARTY_SNAPPY_SNAPPY_STUBS_PUBLIC_H_
#define CPP_THIRD_PARTY_SNAPPY_SNAPPY_STUBS_PUBLIC_H_

#if defined(__linux__)
#include "linux/snappy-stubs-public.h"
#else
#error generate snappy-stubs-public.h for your platform
#endif

#endif  // CPP_THIRD_PARTY_SNAPPY_SNAPPY_STUBS_PUBLIC_H_

