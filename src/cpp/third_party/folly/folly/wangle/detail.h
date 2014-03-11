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

#pragma once

#include <folly/Optional.h>
#include <stdexcept>
#include <atomic>

#include "Try.h"
#include "Promise.h"
#include "Future.h"

namespace folly { namespace wangle { namespace detail {

/** The shared state object for Future and Promise. */
template<typename T>
class FutureObject {
 public:
  FutureObject() = default;

  // not copyable
  FutureObject(FutureObject const&) = delete;
  FutureObject& operator=(FutureObject const&) = delete;

  // not movable (see comment in the implementation of Future::then)
  FutureObject(FutureObject&&) = delete;
  FutureObject& operator=(FutureObject&&) = delete;

  Try<T>& getTry() {
    return *value_;
  }

  template <typename F>
  void setContinuation(F func) {
    if (continuation_) {
      throw std::logic_error("setContinuation called twice");
    }

    if (value_.hasValue()) {
      func(std::move(*value_));
      delete this;
    } else {
      continuation_ = std::move(func);
    }
  }

  void fulfil(Try<T>&& t) {
    if (value_.hasValue()) {
      throw std::logic_error("fulfil called twice");
    }

    if (continuation_) {
      continuation_(std::move(t));
      delete this;
    } else {
      value_ = std::move(t);
    }
  }

  void setException(std::exception_ptr const& e) {
    fulfil(Try<T>(e));
  }

  template <class E> void setException(E const& e) {
    fulfil(Try<T>(std::make_exception_ptr<E>(e)));
  }

  bool ready() const {
    return value_.hasValue();
  }

  typename std::add_lvalue_reference<T>::type value() {
    return value_->value();
  }

 private:
  folly::Optional<Try<T>> value_;
  std::function<void(Try<T>&&)> continuation_;
};

template <typename... Ts>
struct VariadicContext {
  VariadicContext() : total(0), count(0) {}
  Promise<std::tuple<Try<Ts>... > > p;
  std::tuple<Try<Ts>... > results;
  size_t total;
  std::atomic<size_t> count;
  typedef Future<std::tuple<Try<Ts>...>> type;
};

template <typename... Ts, typename THead, typename... Fs>
typename std::enable_if<sizeof...(Fs) == 0, void>::type
whenAllVariadicHelper(VariadicContext<Ts...> *ctx, THead& head, Fs&... tail) {
  head.setContinuation([ctx](Try<typename THead::value_type>&& t) {
    const size_t i = sizeof...(Ts) - sizeof...(Fs) - 1;
    std::get<i>(ctx->results) = std::move(t);
    if (++ctx->count == ctx->total) {
      ctx->p.setValue(std::move(ctx->results));
      delete ctx;
    }
  });
}

template <typename... Ts, typename THead, typename... Fs>
typename std::enable_if<sizeof...(Fs) != 0, void>::type
whenAllVariadicHelper(VariadicContext<Ts...> *ctx, THead& head, Fs&... tail) {
  head.setContinuation([ctx](Try<typename THead::value_type>&& t) {
    const size_t i = sizeof...(Ts) - sizeof...(Fs) - 1;
    std::get<i>(ctx->results) = std::move(t);
    if (++ctx->count == ctx->total) {
      ctx->p.setValue(std::move(ctx->results));
      delete ctx;
    }
  });
  whenAllVariadicHelper(ctx, tail...); // recursive template tail call
}

template <typename T>
struct WhenAllContext {
  explicit WhenAllContext() : count(0), total(0) {}
  Promise<std::vector<Try<T> > > p;
  std::vector<Try<T> > results;
  std::atomic<size_t> count;
  size_t total;
};

template <typename T>
struct WhenAnyContext {
  explicit WhenAnyContext(size_t n) : done(false), ref_count(n) {};
  Promise<std::pair<size_t, Try<T>>> p;
  std::atomic<bool> done;
  std::atomic<size_t> ref_count;
  void decref() {
    if (--ref_count == 0) {
      delete this;
    }
  }
};

}}} // namespace
