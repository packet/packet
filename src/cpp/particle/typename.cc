/*
 * Copyright (C) 2013, The Particle project authors.
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
 * @brief Common utilities for type names.
 *
 * Note: We only support g++.
 *
 * @author Soheil Hassas Yeganeh <soheil@cs.toronto.edu>
 * @version 0.1
 */

#include <ctype.h>
#include <cxxabi.h>
#include <stdlib.h>

#include <regex>
#include <stdexcept>
#include <string>
#include <utility>
#include <vector>

#include "particle/typename.h"

namespace particle {

using std::pair;
using std::regex;
using std::regex_replace;
using std::size_t;
using std::string;
using std::vector;

static void remove_keyword(std::string* str, const std::string& keyword) {
  size_t index = 0;
  size_t keyword_size = keyword.size();
  while ((index = str->find(keyword)) != string::npos) {
    if (index != 0 && isalnum(str->at(index - 1))) {
      continue;
    }

    if (index + keyword_size < str->size() &&
        isalnum(str->at(index + keyword_size))) {
      continue;
    }

    str->erase(index, keyword_size);
    if (index + keyword_size < str->size()) {
      str->erase(index);
    }
    if (index != 0) {
      str->erase(index - 1, 1);
    }
  }
}

static void shorten_type_name(std::string* str) {
  static vector<pair<string, string>> replacement_list {
    {"bool", "@b"},
    {"unsigned char", "@cu"},
    {"char", "@c"},
    {"unsigned short", "@hu"},
    {"short", "@h"},
    {"unsigned int", "@u"},
    {"int", "@i"},
    {"unsigned long", "@lu"},
    {"long", "@l"},
    {"float", "@f"},
    {"double", "@d"},
    {"std::string", "@s"},
    {"std::pair<", "<"}
  };

  for (auto& replacement_pair : replacement_list) {
    // TODO(soheil): This can be replaced with regex_replace, but libstd++ has
    // no support for regex_replace.
    auto& keyword = replacement_pair.first;
    auto start = str->find(keyword);
    if (start == string::npos) {
      continue;
    }
    auto& substitue = replacement_pair.second;
    str->replace(start, keyword.size(), substitue);
  }
}

string demangle_type(const char* type_name, bool drop_const) {
  int error;
  char* demangled_cstr = abi::__cxa_demangle(type_name, nullptr, nullptr,
      &error);

  if (error) {
    throw std::runtime_error(string("Cannot demangle the type: ") + type_name);
  }

  string demangled_name = string(demangled_cstr);
  free(demangled_cstr);

  if (drop_const) {
    remove_keyword(&demangled_name, "const");
  }

  shorten_type_name(&demangled_name);

  return demangled_name;
}

std::string demangle_type(const std::type_info& type_id, bool drop_const) {
  return demangle_type(type_id.name(), drop_const);
}

std::pair<boost::string_ref, boost::string_ref> get_pair_types(
    const std::string& t) {

  auto b_pos = t.find(static_cast<char>(TypeDelimiters::PAIR_BEG));
  if (b_pos == std::string::npos) {
    return std::make_pair(boost::string_ref(), boost::string_ref());
  }

  auto e_pos = t.find(static_cast<char>(TypeDelimiters::PAIR_END));
  if (e_pos == std::string::npos) {
    return std::make_pair(boost::string_ref(), boost::string_ref());
  }

  auto s_pos = t.find(static_cast<char>(TypeDelimiters::PAIR_SEP));
  if (s_pos == std::string::npos) {
    return std::make_pair(boost::string_ref(), boost::string_ref());
  }

  return make_pair(boost::string_ref(t.substr(b_pos + 1, e_pos - 1)),
      boost::string_ref(t.substr(e_pos + 1, s_pos -1)));
}

}  // namespace particle

