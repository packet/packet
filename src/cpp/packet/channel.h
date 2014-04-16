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
 * @brief Packet channels and channel listeners.
 *
 * @author Soheil Hassas Yeganeh <soheil@cs.toronto.edu>
 * @version 0.1
 */

#ifndef CPP_PACKET_CHANNEL_H_
#define CPP_PACKET_CHANNEL_H_

#include <limits.h>

#include <csignal>

#include <algorithm>
#include <atomic>
#include <deque>
#include <ios>
#include <memory>
#include <string>
#include <vector>

#include "boost/intrusive_ptr.hpp"

#include "glog/logging.h"

#include "third_party/libuv/include/uv.h"

#include "particle/ringbuffer.h"
#include "particle/signals.h"

#include "packet/internal/uvhelper.h"
#include "packet/packet.h"

namespace packet {

template <typename Packet, typename Factory>
class Channel {
 public:
  typedef boost::intrusive_ptr<packet::internal::IoVector> SharedIoVector;
  typedef boost::intrusive_ptr<Channel> ChannelPtr;
  typedef boost::intrusive_ptr<const Channel> ConstChannelPtr;
  typedef std::uint64_t ChannelId;
  typedef size_t RefCount;

  ~Channel() {
    auto delete_async = [] (uv_handle_t* handle) {
      auto async = reinterpret_cast<uv_async_t*>(handle);
      delete async;
    };

    if (write_async != nullptr) {
      uv_close(reinterpret_cast<uv_handle_t*>(write_async), delete_async);
    }

    if (close_async != nullptr) {
      uv_close(reinterpret_cast<uv_handle_t*>(close_async), delete_async);
    }
  }

  /**
   * Registers read handler.
   * @param read_handler The read handler.
   */
  void on_read(
      std::function<void(const ChannelPtr&, Packet&&)> read_handler) {
    this->read_handler = read_handler;
  }

  /**
   * Registers error handler.
   * @param error_handler The error handler.
   */
  void on_error(std::function<void(const ChannelPtr&)> error_handler) {
    this->error_handler = error_handler;
  }

  /**
   * Registers close handler.
   * @param close_handler The close handler.
   */
  void on_close(std::function<void(const ChannelPtr&)> close_handler) {
    this->close_handler = close_handler;
  }

  /**
   * Writes a packet on the channel. Note: Channel will own the packet.
   * @param packet The packet.
   */
  bool write(Packet&& packet) {
    if (unlikely(is_closed())) {
      return false;
    }

    auto size = packet.size();
    auto io_vec = packet.get_io_vector();
    WriteReq req{{io_vec->get_buf(), size},  // NOLINT
                 std::move(io_vec->shared_io_vector)};
    if (unlikely(!out_buffer.try_write(std::move(req)))) {
      printf("error %zu\n", out_buffer.guess_size());
      return false;
    }

    if (!write_async_sent.load(std::memory_order_acquire)) {
      write_async_sent.store(true, std::memory_order_release);
      uv_async_send(write_async);
    }

    return true;
  }

  void close() {
    closed.store(true, std::memory_order_release);
    uv_async_send(close_async);
  }

  ChannelId get_id() const { return ChannelId(this); }

 private:
  static const size_t VECTOR_SIZE;
  static const size_t MAX_READ_SIZE;
  static const size_t COPY_THRESH;

  struct WriteReq {
    uv_buf_t buf;
    SharedIoVector vec;
  };

  /**
   * Never use this constructor.
   */
  explicit Channel(Factory packet_factory, uv_loop_t* loop,
                   size_t out_buf_size = 1 << 22)
      : io_vector(nullptr),
        written(0),
        consumed(0),
        close_async(new uv_async_t()),
        write_async(new uv_async_t()),
        packet_factory(packet_factory),
        out_buffer(out_buf_size),
        closed(false),
        write_async_sent(false),
        ref_count(1) {
    stream.data = this;
    uv_tcp_init(loop, &stream);

    close_async->data = this;
    uv_async_init(loop, close_async, [](uv_async_t* async, int status) {
      auto channel = static_cast<Channel*>(async->data);
      if (unlikely(channel == nullptr)) {
        return;
      }

      channel->do_close();
    });

    write_async->data = this;
    uv_async_init(loop, write_async, [](uv_async_t* async, int status) {
      auto channel = static_cast<Channel*>(async->data);
      if (unlikely(channel == nullptr)) {
        return;
      }

      channel->write_async_sent.store(false, std::memory_order_release);
      channel->write_packets();
    });
  }

  RefCount add_ref(RefCount diff = 1,
                   std::memory_order order = std::memory_order_seq_cst) {
    return ref_count.fetch_add(diff, order) + diff;
  }

  RefCount release(RefCount diff = 1,
                   std::memory_order order = std::memory_order_seq_cst) {
    return ref_count.fetch_sub(diff, order) - diff;
  }

  ChannelPtr self() {
    return ChannelPtr(this);
  }

  ConstChannelPtr self() const {
    return ConstChannelPtr(this);
  }

  bool is_closed() {
    return closed.load(std::memory_order_acquire);
  }

  void do_close() {
    call_close_handler();
    closed = true;
    close_stream();
  }

  void close_stream() {
    if (uv_is_closing(reinterpret_cast<uv_handle_t*>(&stream))) {
      return;
    }

    uv_close(reinterpret_cast<uv_handle_t*>(&stream), [](uv_handle_t* handle) {
      auto channel = static_cast<Channel*>(handle->data);
      intrusive_ptr_release(channel);
    });
  }

  void read_packets(size_t size) {
    if (!read_handler || is_closed()) {
      return;
    }

    this->written += size;
    assert(io_vector->size() >= written);

    do {
      size_t consumed = 0;
      assert(this->consumed <= this->written &&
             "We have consumed more data than it's actually written.");

      packet_factory.read_packets(
          IoVector(this->io_vector, this->consumed),
          std::min(this->written - this->consumed, MAX_READ_SIZE),
          [&](Packet&& packet) { this->call_read_handler(std::move(packet)); },
          &consumed);

      this->consumed += consumed;
      assert(this->consumed <= written &&
             "We have consumed more data than it's actually written.");

      if (consumed == 0) {
        break;
      }
    } while (true);

    this->write_packets(IOV_MAX);
  }

  void write_packets(size_t threshold = 0) {
    auto size = out_buffer.guess_size() + out_vectors.size();
    while (size > threshold) {
      auto written = write_a_batch(size);
      if (!written) {
        return;
      }

      if (unlikely(written > size)) {
        return;
      }

      size -= written;
    }
  }

  size_t write_a_batch(size_t batch_size) {
    if (unlikely(!batch_size)) {
      return 0;
    }

    if (uv_is_closing(reinterpret_cast<uv_handle_t*>(&stream))) {
      LOG(ERROR) << "Cannot write on a closing stream.";
      return 0;
    }

    if (batch_size > IOV_MAX) {
      batch_size = IOV_MAX;
    }

    if (out_vectors.size() < batch_size) {
      size_t buffer_size = batch_size - out_vectors.size();

      WriteReq req;
      particle::CpuId last_cpu_id = 0;

      while (buffer_size--) {
        if (!out_buffer.try_read(&req, &last_cpu_id)) {
          continue;
        }

        out_uv_bufs[out_vectors.size()] = std::move(req.buf);
        out_vectors.push_back(std::move(req.vec));
      }
    }

    if (unlikely(out_vectors.empty())) {
      return 0;
    }

    maybe_merge_uv_bufs();

    int written = uv_try_write(reinterpret_cast<uv_stream_t*>(&stream),
                               out_uv_bufs, out_vectors.size());

    if (written < 0) {
      LOG(ERROR) << "Error in write.\n";
      goto ret;
    }

    if (written == 0) {
      return 0;
    }

  ret:
    return clear_out_vectors(written);
  }

  void maybe_merge_uv_bufs() {
    assert(out_vectors.size() && "There is no vectors to merge.");

    const auto begin = &out_uv_bufs[0];  // NOLINT
    const auto end = begin + out_vectors.size();  // NOLINT

    size_t size = 0;
    auto p = end - 1;
    for (; begin <= p && p->len <= COPY_THRESH; --p) {
      size += p->len;
    }

    if (size <= COPY_THRESH) {
      return;
    }

    ++p;

    const auto count = end - p;  // NOLINT
    assert(count > 0 &&
           "There is no buffer to merge but the function did not return");

    auto vec = packet::internal::make_shared_io_vector(size);
    auto buf = vec->get_buf();
    size_t offset = 0;
    for (; p < end; p++) {
      std::memcpy(buf + offset, p->base, p->len);
      offset += p->len;
    }

    auto vec_size = out_vectors.size() - count;
    if (!vec_size) {
      out_vectors.clear();
    } else {
      out_vectors.erase(out_vectors.end() - count, out_vectors.end());
    }

    out_uv_bufs[vec_size] = {buf, size};
    out_vectors.push_back(std::move(vec));
  }

  /**
   * Clears out the vectors that are written and returns the count of those
   * vectors.
   */
  size_t clear_out_vectors(size_t written) {
    assert(out_vectors.size() && "Clearing vectors when there is no out buf.");

    auto buf = &out_uv_bufs[0];
    while (written) {
      if (unlikely(written < buf->len)) {
        // No need to fix buf.
        buf->base += written;
        buf->len -= written;
        break;
      }

      written -= buf->len;

      assert(!out_vectors.empty() &&
             "out_vectors is empty but there is apparently a write.");

      buf++;
      assert(buf <= &out_uv_bufs[out_vectors.size()] &&
             "Buffer ptr accesses an invalid location.");
    }

    const auto bufs_written = buf - &out_uv_bufs[0];  // NOLINT
    assert(bufs_written <= out_vectors.size() &&
           "Written more than what it's requested.");

    const auto size = out_vectors.size() - bufs_written;  // NOLINT
    if (likely(!size)) {
      out_vectors.clear();
    } else {
      out_vectors.erase(out_vectors.begin(),
                        out_vectors.begin() + bufs_written);
      std::memmove(&out_uv_bufs[0], buf, size * sizeof(uv_buf_t));
    }

    return bufs_written;
  }

  /**
   * Consumes the buffer.
   * @param size The number of bytes consumed.
   * Note: Must be called whenever a few bytes in the io_vector are consumed.
   */
  void consume(size_t size) { consumed += size; }

  /** Creates a new IO vector for future reads. */
  void reinitialize_vector() {
    auto new_io_vector =
        packet::internal::make_shared_io_vector(get_new_vector_size());
    new_io_vector->set_metadata(get_id());

    if (unlikely(io_vector == nullptr)) {
      io_vector = new_io_vector;
      consumed = 0;
      written = 0;
      return;
    }

    assert(consumed <= written);

    auto remainder = written - consumed;
    assert(remainder <= new_io_vector->size());
    packet::internal::IoVector::memmove(new_io_vector.get(), 0, io_vector.get(),
                                        consumed, remainder);
    written = remainder;
    consumed = 0;
    io_vector = std::move(new_io_vector);
  }

  size_t get_new_vector_size() {
    if (likely(consumed != 0 || written < VECTOR_SIZE)) {
      return VECTOR_SIZE;
    }

    return VECTOR_SIZE + written;
  }

  static constexpr size_t expand_threshhold() {
    return 3 * VECTOR_SIZE / 4;
  }

  bool should_expand(size_t suggested_size) {
    if (consumed < expand_threshhold()) {
      // Doesn't make sense to expand at this stage.
      return false;
    }

    return written == io_vector->size();
  }

  /** Allocates at least suggested_size from the shared IO vector. */
  void allocate_uv_buf(size_t suggested_size, uv_buf_t* buf) {
    if (unlikely(io_vector == nullptr || should_expand(suggested_size))) {
      reinitialize_vector();
    }

    assert(written <= io_vector->size());

    buf->len = std::min(io_vector->size() - written, VECTOR_SIZE);
    buf->base = buf->len == 0 ? nullptr : io_vector->get_buf(written);
  }

  void start() {
    auto read_cb = [] (uv_stream_t* stream, ssize_t nread,
        const uv_buf_t* buf) {
      auto channel = static_cast<Channel*>(stream->data);
      if (unlikely(channel == nullptr)) {
        return;
      }

      if (unlikely(nread == UV_ENOBUFS)) {
        channel->read_packets(0);
        return;
      }

      if (unlikely(nread < 0 || buf == nullptr || buf->base == nullptr ||
          buf->len == 0)) {
        channel->call_error_handler();
        return;
      }

      channel->read_packets(nread);
    };

    auto alloc_cb = [] (uv_handle_t* handle, size_t suggested_size,
        uv_buf_t* buf) {
      auto channel = static_cast<Channel*>(handle->data);
      if (unlikely(channel == nullptr)) {
        return;
      }

      channel->allocate_uv_buf(suggested_size, buf);
    };

    uv_read_start(reinterpret_cast<uv_stream_t*>(&stream), alloc_cb, read_cb);
  }

  void call_error_handler() {
    if (error_handler) {
      error_handler(self());
    }

    do_close();
  }

  void call_read_handler(Packet&& packet) {
    if (!read_handler) {
      return;
    }

    read_handler(self(), std::move(packet));
  }

  void call_close_handler() {
    if (!close_handler) {
      return;
    }

    close_handler(self());
  }

  /** The IO vector allocated for upcoming reads. */
  SharedIoVector io_vector;

  /** Number of bytes that are read from the socket. */
  size_t written;

  /**
   * Number of bytes that are consumed by previous packets using the same
   * vector.
   *
   * Invariant: consumed <= written.
   */
  size_t consumed;

  /** UV handle representing the channel. */
  uv_tcp_t stream;

  /** Used for closing the channel. */
  uv_async_t* close_async;

  /** Used for writing on the channel. */
  uv_async_t* write_async;

  /** Packet factory used for consuming packets. */
  Factory packet_factory;

  /** The buffer used for outgoing packets. Shared among threads. */
  particle::PerCpuRingBuffer<WriteReq> out_buffer;

  /** The shared io vectors and uv_bufs ready to be written. Not thread safe. */
  uv_buf_t out_uv_bufs[IOV_MAX];
  std::deque<SharedIoVector> out_vectors;

  std::function<void(const ChannelPtr&, Packet&&)> read_handler;
  std::function<void(const ChannelPtr&)> error_handler;
  std::function<void(const ChannelPtr&)> close_handler;

  std::atomic<bool> closed;
  std::atomic<bool> write_async_sent;
  std::atomic<RefCount> ref_count;

  template <typename P, typename F>
  friend class ChannelListener;

  template <typename P, typename F>
  friend class ChannelClient;

  template <typename P, typename F, typename... A>
  friend typename Channel<P, F>::ChannelPtr make_channel(F f, A... a);

  template <typename P, typename F>
  friend void intrusive_ptr_add_ref(Channel<P, F>* channel);

  template <typename P, typename F>
  friend void intrusive_ptr_release(Channel<P, F>* channel);

  template <typename C>
  friend void delete_chan_and_loop(boost::intrusive_ptr<C>* channel,
                                   uv_loop_t* loop);

  FRIEND_TEST(ChannelTest, Allocation);
  FRIEND_TEST(ChannelTest, ClearVectors);
  FRIEND_TEST(ChannelTest, MakeChannel);
  FRIEND_TEST(ChannelTest, ReadPackets);
  FRIEND_TEST(ChannelTest, WritePackets);
  FRIEND_TEST(ChannelTest, WritePacketsPerCpu);
};

template <typename Packet, typename Factory>
const size_t Channel<Packet, Factory>::VECTOR_SIZE = 128 * 1024 - 8;

template <typename Packet, typename Factory>
const size_t Channel<Packet, Factory>::MAX_READ_SIZE = 64 * 1024;

template <typename Packet, typename Factory>
const size_t Channel<Packet, Factory>::COPY_THRESH = 128;

template <typename Packet, typename Factory, typename... Args>
typename Channel<Packet, Factory>::ChannelPtr make_channel(Factory factory,
                                                           Args... args) {
  auto channel = typename Channel<Packet, Factory>::ChannelPtr(
      new Channel<Packet, Factory>(factory, std::forward<Args>(args)...));
  return channel;
}

template <typename Packet, typename Factory>
void intrusive_ptr_add_ref(Channel<Packet, Factory>* channel) {
  channel->add_ref(1, std::memory_order_relaxed);
}

template <typename Packet, typename Factory>
inline void intrusive_ptr_release(Channel<Packet, Factory>* channel) {
  if (channel->release(1, std::memory_order_release) == 0) {
    std::atomic_thread_fence(std::memory_order_acquire);
    delete channel;
  }
}

template <typename Packet, typename Factory = PacketFactory<Packet>>
class ChannelClient final : private packet::internal::UvLoop {
 public:
  typedef typename Channel<Packet, Factory>::ChannelPtr ChannelPtr;

  /**
   * Never call this method.
   * @see make_client_channel.
   */
  explicit ChannelClient(Factory packet_factory)
      : UvLoop(),
        packet_factory(packet_factory),
        stop_async(),
        channel(nullptr),
        connection_handler(),
        cleanup_gaurd([this] { this->stop(); }) {
    stop_async.data = this;
    uv_async_init(&loop, &stop_async, [](uv_async_t* async, int status) {
      if (status) {
        // FIXME(soheil): Log this.
        return;
      }

      auto self = static_cast<ChannelClient*>(async->data);
      if (self->channel != nullptr) {
        self->channel->close();
      }
      self->stop_loop();
    });
  }

  ~ChannelClient() {
    channel.reset();
  }

  /**
   * Registers connection handler.
   * @param handler The connection handler.
   */
  void on_connect(std::function<void(const ChannelPtr&)> handler) {
    connection_handler = handler;
  }
  /**
   * The channel starts connecting to the destination.
   * @param sin The destination address.
   */
  int connect_to(sockaddr_in addr) {
    uv_connect_t connect_req;
    connect_req.data = this;

    channel = make_channel<Packet>(packet_factory, &loop);

    sockaddr* saddr = reinterpret_cast<sockaddr*>(&addr);
    int err = uv_tcp_connect(&connect_req, &channel->stream, saddr,
        [] (uv_connect_t* req, int status) {
          if (status != 0) {
            throw std::ios_base::failure("Cannot connect to the given addr.");
          }

          auto self = static_cast<ChannelClient*>(req->data);

          self->call_connection_handler(self->channel);
          self->channel->start();
        });

    if (err) {
      // FIXME(soheil): Log this.
      return err;
    }

    return start_loop();
  }

  int connect_to(const std::string& host, int port) {
    sockaddr_in addr;
    uv_ip4_addr(host.c_str(), port, &addr);
    return connect_to(addr);
  }

  /**
   * Stops the client and closes the connection if stablished.
   */
  void stop() {
    uv_async_send(&stop_async);
  }

 private:
  void call_connection_handler(const ChannelPtr& channel) {
    if (!connection_handler) {
      return;
    }

    connection_handler(channel);
  }

  /** The packet factory used for reading packets from the stream. */
  Factory packet_factory;

  /** Used for stopping the client. */
  uv_async_t stop_async;

  /** The client channel. */
  ChannelPtr channel;

  /** Handler called when the connection is established. */
  std::function<void(const ChannelPtr& channel)> connection_handler;

  /** The cleanup gaurd for signals. */
  particle::CleanupGaurd cleanup_gaurd;
};

// FIXME(soheil): Does not support ipv6. Fix that. sin should be converted to
// sockaddr.
template <typename Packet, typename Factory = PacketFactory<Packet>>
class ChannelListener final : private packet::internal::UvLoop {
 public:
  static const int DEFUALT_BACKLOG = 1024;

  typedef typename Channel<Packet, Factory>::ChannelPtr ChannelPtr;

  /**
   * @param packet_factory The packet factory.
   * @param sin The listening socket address.
   */
  explicit ChannelListener(Factory packet_factory)
      : packet::internal::UvLoop(),
        server(),
        stop_async(),
        accept_handler(),
        error_handler(),
        packet_factory(packet_factory),
        cleanup_gaurd([this] { this->stop(); }) {
    uv_tcp_init(&loop, &server);
    server.data = this;

    stop_async.data = this;
    uv_async_init(&loop, &stop_async, [](uv_async_t* async, int status) {
      if (status) {
        // FIXME(soheil): Log this.
        return;
      }

      auto self = static_cast<ChannelListener*>(async->data);
      self->stop_loop();
    });
  }

  ~ChannelListener() {
    uv_close(reinterpret_cast<uv_handle_t*>(&stop_async), nullptr);
  }

  /**
   * Stops the listener.
   */
  void stop() {
    uv_async_send(&stop_async);
  }

  /**
   * Registers a handler that is called upon accepting a new connection.
   * @param handler The accept handler.
   */
  void on_accept(std::function<void(const ChannelPtr&)> handler) {
    accept_handler = handler;
  }

  /**
   * Registers a handler that is called when an error occurs.
   * @param handler The error handler.
   */
  void on_error(std::function<void(ChannelListener*)> handler) {  // NOLINT
    error_handler = handler;
  }

  /**
   * Starts listening on the address. This call will be blocked until close()
   * is called.
   */
  int listen(sockaddr_in addr, int backlog = DEFUALT_BACKLOG) {
    // We need to ignore SIGPIPE because libuv can't correctly handle it on
    // Linux.
    particle::ignore_signal(SIGPIPE);

    uv_tcp_bind(&server, reinterpret_cast<sockaddr*>(&addr), 0);
    auto err = uv_listen(reinterpret_cast<uv_stream_t*>(&server), backlog,
                         [](uv_stream_t* server, int status) {
          auto self = static_cast<ChannelListener*>(server->data);

          if (status) {
            self->call_error_handler();
            return;
          }

          auto channel =
              make_channel<Packet>(self->packet_factory, &self->loop);

          auto server_stream = reinterpret_cast<uv_stream_t*>(&self->server);
          auto client_stream = reinterpret_cast<uv_stream_t*>(&channel->stream);

          if (uv_accept(server_stream, client_stream)) {
            // FIXME(soheil): Add logs.
            self->call_error_handler();
            return;
          }

          self->call_accept_handler(channel);

          channel->start();
    });

    if (err) {
      call_error_handler();
      return err;
    }

    return start_loop();
  }

  /**
   * Starts listening on the given address and port.
   */
  int listen(const std::string& host, int port,
      int backlog = DEFUALT_BACKLOG) {
    sockaddr_in addr;
    uv_ip4_addr(host.c_str(), port, &addr);
    return listen(addr, backlog);
  }

 private:
  void call_error_handler() {
    if (!error_handler) {
      return;
    }

    error_handler(this);
  }

  void call_accept_handler(const ChannelPtr& channel) {
    if (!accept_handler) {
      return;
    }

    accept_handler(channel);
  }

  /** The server stream listening on the given address. */
  uv_tcp_t server;

  /** Used for stopping the listener. */
  uv_async_t stop_async;

  /** Invoked when a new channel is accepted. */
  std::function<void(const ChannelPtr&)> accept_handler;  // NOLINT

  /** Invoked when there is an error in the listener. */
  std::function<void(ChannelListener*)> error_handler;  // NOLINT

  /**
   * The packet factory used for reading and writing packets on all channels
   * accepted through this listener.
   */
  Factory packet_factory;

  particle::CleanupGaurd cleanup_gaurd;
};

}  // namespace packet

#endif  // CPP_PACKET_CHANNEL_H_

