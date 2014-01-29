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
 * @brief Unittests for channel.
 *
 * @author Soheil Hassas Yeganeh <soheil@cs.toronto.edu>
 * @version 0.1
 */

#include <chrono>
#include <memory>
#include <thread>

#include "third_party/libuv/include/uv.h"

#include "gtest/gtest.h"

#include "particle/cpu.h"

#include "packet/channel.h"
#include "packet/packet.h"

#include "test/simple.h"

namespace packet {

using simple::AnotherSimple;
using simple::Simple;
using simple::SimpleParent;
using simple::YetAnotherSimple;
using simple::YetYetAnotherSimple;

using std::move;
using std::shared_ptr;
using std::unique_ptr;

class DummyPacket : public Packet {
 public:
  static const size_t SIZE = 2;

  explicit DummyPacket(const IoVector& io_vector) : Packet(io_vector) {}
  explicit DummyPacket(size_t size = SIZE)
      : DummyPacket(make_io_vector(size)) {}

  static size_t size_(const IoVector& io_vector) {
    return io_vector.read_data<uint8_t>(0);
  }

  virtual size_t size() const override {
    return size_(vector);
  }

  void set_size(size_t size) {
    vector.write_data<uint8_t>(uint8_t(size), 0);
  }

  uint8_t get_id() const {
    return vector.read_data<uint8_t>(1);
  }

  void set_id(uint8_t id) {
    vector.write_data<uint8_t>(id, 1);
  }
};

typedef shared_ptr<Channel<DummyPacket>> ChannelPtr;

template <typename Channel>
void dispose_channel(const shared_ptr<Channel>& channel) {
  channel->self.reset();
  delete channel->write_async;
  delete channel->close_async;
  channel->write_async = nullptr;
  channel->close_async = nullptr;
}

TEST(ChannelTest, MakeChannel) {
  auto packet_factory = make_packet_factory<DummyPacket>();
  auto loop = uv_loop_new();
  auto dummy_channel = make_channel<DummyPacket>(packet_factory, loop);
  EXPECT_NE(nullptr, dummy_channel);
  uv_loop_delete(loop);
  dispose_channel(dummy_channel);
}

TEST(ChannelTest, Allocation) {
  auto packet_factory = make_packet_factory<DummyPacket>();
  auto loop = uv_loop_new();
  auto dummy_channel = make_channel<DummyPacket>(packet_factory, loop);
  EXPECT_NE(nullptr, dummy_channel);

  const size_t buffer_size = Channel<DummyPacket>::MAX_READ_SIZE;

  uv_buf_t buf;
  dummy_channel->allocate_uv_buf(buffer_size, &buf);
  EXPECT_NE(nullptr, buf.base);
  EXPECT_EQ(Channel<DummyPacket>::VECTOR_SIZE, buf.len);

  dummy_channel->allocate_uv_buf(buffer_size, &buf);
  EXPECT_NE(nullptr, buf.base);
  EXPECT_EQ(Channel<DummyPacket>::VECTOR_SIZE, buf.len);

  dummy_channel->written += Channel<DummyPacket>::VECTOR_SIZE - 1;

  auto old_vector = dummy_channel->io_vector;

  dummy_channel->allocate_uv_buf(1, &buf);
  EXPECT_NE(nullptr, buf.base);
  EXPECT_EQ(size_t(1), buf.len);
  EXPECT_EQ(old_vector, dummy_channel->io_vector);

  dummy_channel->written = dummy_channel->io_vector->size();
  dummy_channel->consumed = dummy_channel->written;

  dummy_channel->allocate_uv_buf(1, &buf);
  EXPECT_NE(nullptr, buf.base);
  EXPECT_NE(old_vector, dummy_channel->io_vector);
  EXPECT_EQ(Channel<DummyPacket>::VECTOR_SIZE, buf.len);
  EXPECT_EQ(Channel<DummyPacket>::VECTOR_SIZE,
            dummy_channel->io_vector->size());

  old_vector = dummy_channel->io_vector;

  dummy_channel->written = dummy_channel->io_vector->size();
  dummy_channel->consumed = 0;

  dummy_channel->allocate_uv_buf(1, &buf);
  EXPECT_NE(nullptr, buf.base);
  EXPECT_NE(old_vector, dummy_channel->io_vector);
  EXPECT_EQ(Channel<DummyPacket>::VECTOR_SIZE, buf.len);
  EXPECT_NE(Channel<DummyPacket>::VECTOR_SIZE,
            dummy_channel->io_vector->size());

  uv_loop_delete(loop);

  dispose_channel(dummy_channel);
}

TEST(ChannelTest, ReadPackets) {
  auto packet_factory = make_packet_factory<DummyPacket>();
  auto loop = uv_loop_new();
  auto dummy_channel = make_channel<DummyPacket>(packet_factory, loop);
  EXPECT_NE(nullptr, dummy_channel);

  const size_t packet_size = 2;
  const size_t packet_count = 48;
  const size_t buffer_size = packet_count * packet_size;
  uv_buf_t buf;

  dummy_channel->allocate_uv_buf(buffer_size, &buf);

  EXPECT_TRUE(buf.len <= Channel<DummyPacket>::VECTOR_SIZE);

  std::memset(buf.base, packet_size, buffer_size);

  size_t read_packet_count = 0;
  size_t read_packet_size = 0;

  dummy_channel->on_read([&](const ChannelPtr& channel,
                             const DummyPacket& packet) {
    EXPECT_NE(uint64_t(0), packet.get_metadata());
    read_packet_count++;
    read_packet_size += packet.size();
  });

  dummy_channel->read_packets(buffer_size);

  EXPECT_EQ(packet_count, read_packet_count);
  EXPECT_EQ(buffer_size, read_packet_size);

  uv_loop_delete(loop);

  dispose_channel(dummy_channel);
}

TEST(ChannelTest, WritePackets) {
  auto packet_factory = make_packet_factory<DummyPacket>();
  auto loop = uv_loop_new();
  auto dummy_channel = make_channel<DummyPacket>(packet_factory, loop);
  EXPECT_NE(nullptr, dummy_channel);

  const uint8_t ID = 2;
  DummyPacket w_p(2);
  w_p.set_id(ID);
  EXPECT_TRUE(dummy_channel->write(move(w_p)));
  EXPECT_EQ(size_t(1), dummy_channel->out_buffer.guess_size());

  DummyPacket r_p(2);
  EXPECT_TRUE(dummy_channel->out_buffer.try_read(&r_p));
  EXPECT_EQ(ID, r_p.get_id());

  uv_loop_delete(loop);

  dispose_channel(dummy_channel);
}

TEST(ChannelTest, WritePacketsPerCpu) {
  auto packet_factory = make_packet_factory<DummyPacket>();
  auto loop = uv_loop_new();
  auto dummy_channel = make_channel<DummyPacket>(packet_factory, loop);
  EXPECT_NE(nullptr, dummy_channel);

  const uint8_t ID = 2;

  const size_t cpu_count = dummy_channel->out_buffer.get_cpu_count();
  for (size_t i = 0; i < cpu_count; i++) {
    std::thread([&] {
      EXPECT_EQ(0, particle::set_cpu_affinity(i));
      EXPECT_EQ(i, (particle::get_cached_cpu_of_this_thread()));

      DummyPacket w_p(2);
      w_p.set_id(ID);
      EXPECT_TRUE(dummy_channel->write(move(w_p)));
      EXPECT_EQ(size_t(1), dummy_channel->out_buffer.guess_size(i));
    }).join();
  }

  EXPECT_EQ(cpu_count, dummy_channel->out_buffer.guess_size());

  for (size_t i = 0; i < cpu_count; i++) {
    DummyPacket r_p(2);
    particle::CpuId cpu_id = 0;
    EXPECT_TRUE(dummy_channel->out_buffer.try_read(&r_p, &cpu_id));
    EXPECT_EQ(ID, r_p.get_id());
  }

  EXPECT_EQ(size_t(0), dummy_channel->out_buffer.guess_size());

  uv_loop_delete(loop);

  dispose_channel(dummy_channel);
}

TEST(ChannelListener, MakeListener) {
}

TEST(ChannelClient, MakeClient) {
}

TEST(ChannelIntegration, ServerClose) {
  const int CLOSED_ERR_CODE = 1;
  const std::string HOST = "127.0.0.1";
  const int PORT = 22222;

  auto packet_factory = make_packet_factory<DummyPacket>();

  auto th_listener = std::thread([&]() {
    ChannelListener<DummyPacket> listener(packet_factory);
    listener.on_accept([&](const ChannelPtr& channel) {
      channel->close();
      listener.stop();
    });
    auto err = listener.listen(HOST, PORT);
    EXPECT_EQ(CLOSED_ERR_CODE, err);
  });

  auto th_client = std::thread([&]() {
    std::chrono::milliseconds duration(2000);
    std::this_thread::sleep_for(duration);

    ChannelClient<DummyPacket> client(packet_factory);
    client.on_connect([&](const ChannelPtr& channel) {
      channel->on_error([&](const ChannelPtr& channel) { client.stop(); });  // NOLINT
    });
    auto err = client.connect_to(HOST, PORT);
    EXPECT_EQ(CLOSED_ERR_CODE, err);
  });

  th_client.join();
  th_listener.join();
}

DummyPacket make_dummy_packet(uint8_t id) {
  DummyPacket p;
  p.set_size(DummyPacket::SIZE);
  p.set_id(id);
  return p;
}

TEST(ChannelIntegration, PingPong) {
  const int CLOSED_ERR_CODE = 1;
  const std::string HOST = "127.0.0.1";
  const int PORT = 22223;

  const uint8_t PING_ID = 1;
  const uint8_t PONG_ID = 2;

  auto packet_factory = make_packet_factory<DummyPacket>();

  auto th_listener = std::thread([&]() {
    uint8_t current_id = PING_ID;
    ChannelListener<DummyPacket> listener(packet_factory);
    listener.on_accept([&](const ChannelPtr& channel) {
      channel->on_read([&](const ChannelPtr& channel, const DummyPacket& ping) {
        EXPECT_EQ(current_id, ping.get_id());

        if (current_id == PONG_ID) {
          channel->close();
          return;
        }

        current_id = PONG_ID;
        // Test for thread affinity and per cpu buffer.
        std::thread([&] {
                      EXPECT_EQ(0,
                                particle::set_cpu_affinity(
                                    std::thread::hardware_concurrency() - 1));

                      channel->write(make_dummy_packet(PONG_ID));
                    }).join();
      });

      channel->on_error([&](const ChannelPtr& channel) { EXPECT_TRUE(false); });  // NOLINT

      channel->on_close([&](const ChannelPtr& channel) { listener.stop(); });  // NOLINT
    });
    auto err = listener.listen(HOST, PORT);
    EXPECT_EQ(CLOSED_ERR_CODE, err);
    if (err != CLOSED_ERR_CODE) {
      printf("Listener error: %s\n", uv_strerror(err));
    }
  });

  auto th_client = std::thread([&]() {
    std::chrono::milliseconds duration(2000);
    std::this_thread::sleep_for(duration);

    ChannelClient<DummyPacket> client(packet_factory);
    client.on_connect([&](const ChannelPtr& channel) {
      channel->on_read([&](const ChannelPtr& channel, const DummyPacket& pong) {
        EXPECT_EQ(PONG_ID, pong.get_id());

        channel->write(make_dummy_packet(PONG_ID));
      });

      channel->on_close([&](const ChannelPtr& channel) { client.stop(); });  // NOLINT

      // Test for thread affinity and per cpu buffer.
      std::thread([&] {
                    EXPECT_EQ(0, particle::set_cpu_affinity(
                                     std::thread::hardware_concurrency() - 1));

                    channel->write(make_dummy_packet(PING_ID));
                  }).join();
    });
    auto err = client.connect_to(HOST, PORT);
    EXPECT_EQ(CLOSED_ERR_CODE, err);
  });

  th_client.join();
  th_listener.join();
}

TEST(ChannelIntegration, ReliableMessaging) {
  const int CLOSED_ERR_CODE = 1;
  const std::string HOST = "127.0.0.1";
  const int PORT = 22224;
  const uint8_t MAX_ID = 10;

  auto packet_factory = make_packet_factory<DummyPacket>();

  auto th_listener = std::thread([&]() {
    uint8_t current_number = 0;

    ChannelListener<DummyPacket> listener(packet_factory);
    listener.on_accept([&](const ChannelPtr& channel) {
      channel->on_read([&](const ChannelPtr& channel,
                           const DummyPacket& message) {
        EXPECT_EQ(current_number, message.get_id());

        channel->write(make_dummy_packet(current_number));
        current_number++;
      });

      channel->on_close([&](const ChannelPtr& channel) { listener.stop(); });  // NOLINT
    });
    auto err = listener.listen(HOST, PORT);
    EXPECT_EQ(CLOSED_ERR_CODE, err);
    if (err != CLOSED_ERR_CODE) {
      printf("Listener error: %s\n", uv_strerror(err));
    }
  });

  auto th_client = std::thread([&]() {
    std::chrono::milliseconds duration(2000);
    std::this_thread::sleep_for(duration);

    uint8_t current_number = 0;

    ChannelClient<DummyPacket> client(packet_factory);
    client.on_connect([&](const ChannelPtr& channel) {
      channel->on_read([&](const ChannelPtr& channel,
                           const DummyPacket& message) {
        EXPECT_EQ(current_number, message.get_id());

        if (current_number == MAX_ID) {
          channel->close();
          return;
        }

        current_number++;
        channel->write(make_dummy_packet(current_number));
      });

      channel->on_error([&](const ChannelPtr& channel) { EXPECT_TRUE(false); });  // NOLINT

      channel->on_close([&](const ChannelPtr& channel) { client.stop(); });  // NOLINT

      channel->write(make_dummy_packet(current_number));
    });
    auto err = client.connect_to(HOST, PORT);
    EXPECT_EQ(CLOSED_ERR_CODE, err);
  });

  th_client.join();
  th_listener.join();
}

YetAnotherSimple make_yet_another_simple(int simples_count) {
  YetAnotherSimple container(100);
  for (auto i = 0; i < simples_count; i++) {
    container.add_simples(Simple());
  }
  return container;
}

YetYetAnotherSimple make_yetyet_another_simple(int a_count) {
  YetYetAnotherSimple container(100);
  for (auto i = 0; i < a_count; i++) {
    auto a = AnotherSimple(10);
    a.set_y(Simple());
    container.add_a(move(a));
  }
  return container;
}

void check_yet_another_simple(const YetAnotherSimple& pkt) {
  EXPECT_NE(0, pkt.get_s());
  EXPECT_EQ(size_t(pkt.get_s()), pkt.get_simples().size());

  for (auto& simple : pkt.get_simples()) {
    EXPECT_EQ(uint8_t(1), simple.get_x());
  }
}

void check_yetyet_another_simple(const YetYetAnotherSimple& pkt) {
  EXPECT_NE(0, pkt.get_s());
  EXPECT_EQ(size_t(pkt.get_s() / 3), pkt.get_a().size());
}


TEST(ChannelIntegration, PingPongGeneratedPackets) {
  typedef shared_ptr<Channel<SimpleParent>> ChannelPtr;

  const int CLOSED_ERR_CODE = 1;
  const std::string HOST = "127.0.0.1";
  const int PORT = 22225;

  auto packet_factory = make_packet_factory<SimpleParent>();

  auto th_listener = std::thread([&]() {
    ChannelListener<SimpleParent> listener(packet_factory);
    listener.on_accept([&](const ChannelPtr& channel) {
      channel->on_read([&](const ChannelPtr& channel, const SimpleParent& pkt) {
        auto is_pong = simple::is_YetYetAnotherSimple(*pkt.get_io_vector());

        if (is_pong) {
          check_yetyet_another_simple(cast_to_YetYetAnotherSimple(pkt));
          channel->close();
          return;
        }

        check_yet_another_simple(cast_to_YetAnotherSimple(pkt));
        channel->write(make_yetyet_another_simple(2));
      });

      channel->on_error([&](const ChannelPtr& channel) { EXPECT_TRUE(false); });  // NOLINT

      channel->on_close([&](const ChannelPtr& channel) { listener.stop(); });  // NOLINT
    });
    auto err = listener.listen(HOST, PORT);
    EXPECT_EQ(CLOSED_ERR_CODE, err);
    if (err != CLOSED_ERR_CODE) {
      printf("Listener error: %s\n", uv_strerror(err));
    }
  });

  auto th_client = std::thread([&]() {
    std::chrono::milliseconds duration(2000);
    std::this_thread::sleep_for(duration);

    ChannelClient<SimpleParent> client(packet_factory);
    client.on_connect([&](const ChannelPtr& channel) {
      channel->on_read([&](const ChannelPtr& channel,
                           const SimpleParent& pkt) {
        ASSERT_TRUE(simple::is_YetYetAnotherSimple(*pkt.get_io_vector()));

        check_yetyet_another_simple(cast_to_YetYetAnotherSimple(pkt));
        channel->write(make_yetyet_another_simple(2));
      });

      channel->on_close([&](const ChannelPtr& channel) { client.stop(); });  // NOLINT

      channel->write(make_yet_another_simple(2));
    });
    auto err = client.connect_to(HOST, PORT);
    EXPECT_EQ(CLOSED_ERR_CODE, err);
  });

  th_client.join();
  th_listener.join();
}


}  // namespace packet

