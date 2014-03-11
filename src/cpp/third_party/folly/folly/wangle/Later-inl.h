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

#include "folly/wangle/Executor.h"
#include "folly/wangle/Future.h"
#include "folly/Optional.h"

namespace folly { namespace wangle {

template <typename T>
struct isLater {
  static const bool value = false;
};

template <typename T>
struct isLater<Later<T> > {
  static const bool value = true;
};

template <typename T>
struct isLaterOrFuture {
  static const bool value = false;
};

template <typename T>
struct isLaterOrFuture<Later<T>> {
  static const bool value = true;
};

template <typename T>
struct isLaterOrFuture<Future<T>> {
  static const bool value = true;
};

template <typename T>
template <class U, class Unused, class Unused2>
Later<T>::Later() {
  future_ = starter_.getFuture();
}

template <typename T>
Later<T>::Later(Promise<void>&& starter)
  : starter_(std::forward<Promise<void>>(starter)) { }

template <class T>
template <class U, class Unused, class Unused2>
Later<T>::Later(U&& input) {
  folly::MoveWrapper<Promise<U>> promise;
  folly::MoveWrapper<U> inputm(std::forward<U>(input));
  future_ = promise->getFuture();
  starter_.getFuture().then([=](Try<void>&& t) mutable {
    promise->setValue(std::move(*inputm));
  });
}

template <class T>
template <class F>
typename std::enable_if<
  !isLaterOrFuture<typename std::result_of<F(Try<T>&&)>::type>::value,
  Later<typename std::result_of<F(Try<T>&&)>::type> >::type
Later<T>::then(F&& fn) {
  typedef typename std::result_of<F(Try<T>&&)>::type B;

  Later<B> later(std::move(starter_));
  later.future_ = future_->then(std::forward<F>(fn));
  return later;
}

template <class T>
template <class F>
typename std::enable_if<
  isFuture<typename std::result_of<F(Try<T>&&)>::type>::value,
  Later<typename std::result_of<F(Try<T>&&)>::type::value_type> >::type
Later<T>::then(F&& fn) {
  typedef typename std::result_of<F(Try<T>&&)>::type::value_type B;

  Later<B> later(std::move(starter_));
  later.future_ = future_->then(std::move(fn));
  return later;
}

template <class T>
template <class F>
typename std::enable_if<
  isLater<typename std::result_of<F(Try<T>&&)>::type>::value,
  Later<typename std::result_of<F(Try<T>&&)>::type::value_type> >::type
Later<T>::then(F&& fn) {
  typedef typename std::result_of<F(Try<T>&&)>::type::value_type B;

  folly::MoveWrapper<Promise<B>> promise;
  folly::MoveWrapper<F> fnm(std::move(fn));
  Later<B> later(std::move(starter_));
  later.future_ = promise->getFuture();
  future_->then([=](Try<T>&& t) mutable {
    (*fnm)(std::move(t))
    .then([=](Try<B>&& t2) mutable {
      promise->fulfilTry(std::move(t2));
    })
    .launch();
  });
  return later;
}

template <class T>
Later<T> Later<T>::via(Executor* executor) {
  Promise<T> promise;
  Later<T> later(std::move(starter_));
  later.future_ = promise.getFuture();
  future_->executeWith(executor, std::move(promise));
  return later;
}

template <class T>
Future<T> Later<T>::launch() {
  starter_.setValue();
  return std::move(*future_);
}

template <class T>
void Later<T>::fireAndForget() {
  future_->setContinuation([] (Try<T>&& t) {}); // detach
  starter_.setValue();
}

}}
