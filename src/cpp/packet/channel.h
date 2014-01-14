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
#include <ios>
#include <memory>
#include <string>
#include <vector>

#include "glog/logging.h"

#include "third_party/libuv/include/uv.h"

#include "particle/ringbuffer.h"
#include "particle/signals.h"

#include "packet/internal/uvhelper.h"
#include "packet/packet.h"

namespace packet {

template <typename Packet, typename Factory>
class Channel
    : public std::enable_shared_from_this<Channel<Packet, Factory>> {
 public:
  typedef boost::intrusive_ptr<packet::internal::IoVector> SharedIoVector;
  typedef std::shared_ptr<Channel> ChannelPtr;
  typedef std::shared_ptr<const Channel> ConstChannelPtr;
  typedef std::uint64_t ChannelId;

  /**
   * Never use this constructor. It's just public because of std::make_shared.
   */
  explicit Channel(Factory packet_factory, uv_loop_t* loop,
                   size_t out_buf_size = 2 << 12)
      : std::enable_shared_from_this<Channel>(),
        io_vector(nullptr),
        written(0),
        consumed(0),
        stream(),
        close_async(new uv_async_t()),
        write_async(new uv_async_t()),
        packet_factory(packet_factory),
        out_buffer(out_buf_size),
        read_handler(),
        close_handler(),
        self(nullptr),
        closed(false) {
    stream.data = this;
    uv_tcp_init(loop, &stream);

    close_async->data = this;
    uv_async_init(loop, close_async, [](uv_async_t* async, int status) {
      auto channel = static_cast<Channel*>(async->data)->self;
      if (unlikely(channel == nullptr)) {
        return;
      }

      channel->do_close();
    });

    write_async->data = this;
    uv_async_init(loop, write_async, [](uv_async_t* async, int status) {
      auto channel = static_cast<Channel*>(async->data)->self;
      if (unlikely(channel == nullptr)) {
        return;
      }

      channel->write_packets();
    });
  }

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
      std::function<void(const ChannelPtr&, const Packet&)> read_handler) {
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

    if (unlikely(!out_buffer.try_write(packet))) {
      printf("error\n");
      return false;
    }

    uv_async_send(write_async);
    return true;
  }

  void close() {
    closed = true;
    uv_async_send(close_async);
  }

  ChannelId get_id() const { return ChannelId(this); }

 private:
  static const size_t VECTOR_SIZE;
  static const size_t MAX_READ_SIZE;

  bool is_closed() {
    return closed;
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
      channel->self.reset();
    });
  }

  void read_packets(size_t size) {
    if (!read_handler || is_closed()) {
      return;
    }

    this->written += size;
    assert(io_vector->size() >= written);

    IoVector io_vector(this->io_vector, this->consumed);

    size_t consumed = 0;

    assert(this->consumed <= this->written &&
           "We have consumed more data than it's actually written.");

    packet_factory.read_packets(
        &io_vector, this->written - this->consumed,
        [&](const Packet& packet) { this->call_read_handler(packet); },
        &consumed);

    this->consumed += consumed;
    assert(this->consumed <= written);
  }

  void write_packets() {
    size_t buffer_size = std::min((size_t) IOV_MAX, out_buffer.guess_size());
    auto packets = new std::vector<Packet>();
    packets->reserve(buffer_size);

    size_t consumed = 0;
    Packet packet(make_io_vector(nullptr));
    particle::CpuId last_cpu_id = 0;
    for (; consumed < buffer_size; consumed++) {
      if (!out_buffer.try_read(&packet, &last_cpu_id)) {
        break;
      }
      packets->push_back(std::move(packet));
    }

    if (!consumed) {
      return;
    }

    uv_write_t* write_req = new uv_write_t();
    write_req->data = static_cast<void*>(packets);

    uv_buf_t bufs[IOV_MAX];
    for (size_t j = 0; j < consumed; j++) {
      bufs[j].base = (*packets)[j].get_io_vector()->get_buf();
      bufs[j].len = (*packets)[j].size();
    }

    auto channel_after_write_cb = [](uv_write_t* req, int status) {
      if (status == UV_ECANCELED) {
        LOG(ERROR) << "Write cancelled";
      }

      if (status < 0) {
        LOG(ERROR) << "Error in write";
      }


      auto packets = static_cast<std::vector<Packet>*>(req->data);
      delete packets;
      delete req;
    };

    if (is_closed() ||
        uv_write(write_req, reinterpret_cast<uv_stream_t*>(&stream), bufs,
                 consumed, channel_after_write_cb)) {
      LOG(ERROR) << "Error in write.\n";
      delete packets;
      delete write_req;
    }
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
    packet::internal::IoVector::memmove(new_io_vector.get(), 0,
        io_vector.get(), consumed, remainder);
    written = remainder;
    consumed = 0;
    io_vector = new_io_vector;
  }

  size_t get_new_vector_size() {
    if (likely(consumed != 0 || written < VECTOR_SIZE)) {
      return VECTOR_SIZE;
    }

    return VECTOR_SIZE + written;
  }

  bool out_of_space(size_t suggested_size) {
    return written == io_vector->size();
  }

  /** Allocates at least suggested_size from the shared IO vector. */
  void allocate_uv_buf(size_t suggested_size, uv_buf_t* buf) {
    if (unlikely(io_vector == nullptr || out_of_space(suggested_size))) {
      reinitialize_vector();
    }

    buf->base = io_vector->get_buf(written);
    buf->len = std::min(io_vector->size() - written, MAX_READ_SIZE);
  }

  void start() {
    auto read_cb = [] (uv_stream_t* stream, ssize_t nread,
        const uv_buf_t* buf) {
      auto channel = static_cast<Channel*>(stream->data)->self;
      if (unlikely(channel == nullptr)) {
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
      auto channel = static_cast<Channel*>(handle->data)->self;
      if (unlikely(channel == nullptr)) {
        return;
      }

      channel->allocate_uv_buf(suggested_size, buf);
    };

    uv_read_start(reinterpret_cast<uv_stream_t*>(&stream), alloc_cb, read_cb);
  }

  void call_error_handler() {
    if (error_handler) {
      error_handler(self);
    }

    do_close();
  }

  void call_read_handler(const Packet& packet) {
    if (!read_handler) {
      return;
    }

    read_handler(self, packet);
  }

  void call_close_handler() {
    if (!close_handler) {
      return;
    }

    close_handler(self);
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

  /** The buffer used for outgoing packets. */
  particle::PerCpuRingBuffer<Packet> out_buffer;

  // TODO(soheil): Write a light weight functor. We don't really need such a
  //               structure. Then explain why we didn't use std::fucntion,
  //               here.
  std::function<void(const ChannelPtr&, const Packet&)> read_handler;
  std::function<void(const ChannelPtr&)> error_handler;
  std::function<void(const ChannelPtr&)> close_handler;

  std::shared_ptr<Channel> self;
  std::atomic<bool> closed;

  template <typename P, typename F>
  friend class ChannelListener;

  template <typename P, typename F>
  friend class ChannelClient;

  template <typename P, typename F, typename... A>
  friend std::shared_ptr<Channel<P, F>> make_channel(F f, A... args);

  template <typename C>
  friend void dispose_channel(const std::shared_ptr<C>& channel);

  FRIEND_TEST(ChannelTest, Allocation);
  FRIEND_TEST(ChannelTest, MakeChannel);
  FRIEND_TEST(ChannelTest, ReadPackets);
  FRIEND_TEST(ChannelTest, WritePackets);
  FRIEND_TEST(ChannelTest, WritePacketsPerCpu);
};

template <typename Packet, typename Factory>
const size_t Channel<Packet, Factory>::VECTOR_SIZE = 4 * 1024 - 8;

template <typename Packet, typename Factory>
const size_t Channel<Packet, Factory>::MAX_READ_SIZE = 2048;

template <typename Packet, typename Factory, typename... Args>
std::shared_ptr<Channel<Packet, Factory>> make_channel(Factory factory,
                                                       Args... args) {
  auto channel = std::make_shared<Channel<Packet, Factory>>(
      factory, std::forward<Args>(args)...);
  channel->self = channel;
  return channel;
}

template <typename Packet, typename Factory = PacketFactory<Packet>>
class ChannelClient final : private packet::internal::UvLoop {
 public:
  typedef std::shared_ptr<Channel<Packet, Factory>> ChannelPtr;

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
    uv_async_init(loop, &stop_async, [](uv_async_t* async, int status) {
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
    channel->self.reset();
    channel.reset();

    delete_loop();
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

    channel = make_channel<Packet>(packet_factory, loop);

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

  typedef std::shared_ptr<Channel<Packet, Factory>> ChannelPtr;

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
    uv_tcp_init(loop, &server);
    server.data = this;

    stop_async.data = this;
    uv_async_init(loop, &stop_async, [](uv_async_t* async, int status) {
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
    delete_loop();
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

    uv_tcp_bind(&server, reinterpret_cast<sockaddr*>(&addr));
    auto err = uv_listen(reinterpret_cast<uv_stream_t*>(&server), backlog,
        [] (uv_stream_t* server, int status) {
          auto self = static_cast<ChannelListener*>(server->data);

          if (status) {
            self->call_error_handler();
            return;
          }

          auto channel = make_channel<Packet>(self->packet_factory, self->loop);

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

