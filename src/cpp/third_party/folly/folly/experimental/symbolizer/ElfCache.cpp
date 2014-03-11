/*
 * Copyright 2014 Facebook, Inc.
 *
 * Licensed under the Apache License, Version 2.0 (the "License");
 * you may not use this file except in compliance with the License.
 * You may obtain a copy of the License at
 *
 *   http://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS,
 * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 * See the License for the specific language governing permissions and
 * limitations under the License.
 */

#include "folly/experimental/symbolizer/ElfCache.h"

namespace folly { namespace symbolizer {

SignalSafeElfCache::SignalSafeElfCache(size_t capacity) {
  map_.reserve(capacity);
  slots_.reserve(capacity);

  // Preallocate
  for (size_t i = 0; i < capacity; ++i) {
    slots_.push_back(std::make_shared<ElfFile>());
  }
}

std::shared_ptr<ElfFile> SignalSafeElfCache::getFile(StringPiece p) {
  if (p.size() > Path::kMaxSize) {
    return nullptr;
  }

  Path path(p);
  auto pos = map_.find(path);
  if (pos != map_.end()) {
    return slots_[pos->second];
  }

  size_t n = map_.size();
  if (n >= slots_.size()) {
    DCHECK_EQ(map_.size(), slots_.size());
    return nullptr;
  }

  auto& f = slots_[n];
  if (f->openNoThrow(path.data()) == -1) {
    return nullptr;
  }

  map_[path] = n;
  return f;
}

ElfCache::ElfCache(size_t capacity) : capacity_(capacity) { }

std::shared_ptr<ElfFile> ElfCache::getFile(StringPiece p) {
  auto path = p.str();

  std::lock_guard<std::mutex> lock(mutex_);

  auto pos = files_.find(path);
  if (pos != files_.end()) {
    // Found, move to back (MRU)
    auto& entry = pos->second;
    lruList_.erase(lruList_.iterator_to(*entry));
    lruList_.push_back(*entry);
    return filePtr(entry);
  }

  auto entry = std::make_shared<Entry>();

  // No negative caching
  if (entry->file.openNoThrow(path.c_str()) == -1) {
    return nullptr;
  }

  if (files_.size() == capacity_) {
    // Evict LRU
    lruList_.pop_front();
  }

  files_.emplace(std::move(path), entry);
  lruList_.push_back(*entry);

  return filePtr(entry);
}

std::shared_ptr<ElfFile> ElfCache::filePtr(const std::shared_ptr<Entry>& e) {
  // share ownership
  return std::shared_ptr<ElfFile>(e, &e->file);
}

}}  // namespaces

