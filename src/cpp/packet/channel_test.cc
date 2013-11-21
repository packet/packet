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

#include "packet/channel.h"
#include "packet/packet.h"

#include "test/simple.h"

namespace packet {

using std::dynamic_pointer_cast;
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
typedef shared_ptr<const DummyPacket> PacketPtr;

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

  const size_t buffer_size = 1024;

  uv_buf_t buf;
  dummy_channel->allocate_uv_buf(buffer_size, &buf);
  EXPECT_NE(nullptr, buf.base);
  EXPECT_EQ(dummy_channel->io_vector->size(), buf.len);

  dummy_channel->allocate_uv_buf(buffer_size, &buf);
  EXPECT_NE(nullptr, buf.base);
  EXPECT_EQ(dummy_channel->io_vector->size(), buf.len);

  dummy_channel->written += buffer_size;

  dummy_channel->allocate_uv_buf(buffer_size, &buf);
  EXPECT_NE(nullptr, buf.base);
  EXPECT_EQ(dummy_channel->io_vector->size() - buffer_size, buf.len);

  auto old_vector = dummy_channel->io_vector;

  dummy_channel->written = dummy_channel->io_vector->size() - buffer_size + 1;
  dummy_channel->consumed = 0;

  dummy_channel->allocate_uv_buf(dummy_channel->io_vector->size() + 1, &buf);
  EXPECT_NE(nullptr, buf.base);
  EXPECT_EQ(old_vector, dummy_channel->io_vector);
  EXPECT_EQ(dummy_channel->io_vector->size() - dummy_channel->written, buf.len);

  dummy_channel->allocate_uv_buf(buffer_size, &buf);
  EXPECT_NE(nullptr, buf.base);
  EXPECT_NE(old_vector, dummy_channel->io_vector);
  EXPECT_EQ(dummy_channel->io_vector->size() - dummy_channel->written, buf.len);

  dummy_channel->written = dummy_channel->io_vector->size() - buffer_size + 1;
  dummy_channel->consumed = dummy_channel->written;

  dummy_channel->allocate_uv_buf(buffer_size, &buf);
  EXPECT_NE(nullptr, buf.base);
  EXPECT_NE(old_vector, dummy_channel->io_vector);
  EXPECT_EQ(dummy_channel->io_vector->size(), buf.len);

  uv_loop_delete(loop);

  dispose_channel(dummy_channel);
}

TEST(ChannelTest, ReadPackets) {
  auto packet_factory = make_packet_factory<DummyPacket>();
  auto loop = uv_loop_new();
  auto dummy_channel = make_channel<DummyPacket>(packet_factory, loop);
  EXPECT_NE(nullptr, dummy_channel);

  const size_t packet_size = 2;
  const size_t packet_count = 1024;
  const size_t buffer_size = packet_count * packet_size;
  uv_buf_t buf;

  dummy_channel->allocate_uv_buf(buffer_size, &buf);

  EXPECT_TRUE(buf.len >= buffer_size);

  std::memset(buf.base, packet_size, buffer_size);

  size_t read_packet_count = 0;
  size_t read_packet_size = 0;

  dummy_channel->on_read([&](const ChannelPtr& channel,
                             const PacketPtr& packet) {
    EXPECT_NE(uint64_t(0), packet->get_metadata());
    read_packet_count++;
    read_packet_size += packet->size();
  });

  dummy_channel->read_packets(buffer_size);

  EXPECT_EQ(packet_count, read_packet_count);
  EXPECT_EQ(buffer_size, read_packet_size);

  uv_loop_delete(loop);

  dispose_channel(dummy_channel);
}

TEST(ChannelTest, WritePackets) {
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
      channel->on_error([&](const ChannelPtr& channel) { client.stop(); });
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
      channel->on_read([&](const ChannelPtr& channel, const PacketPtr& ping) {
        EXPECT_EQ(current_id, ping->get_id());

        if (current_id == PONG_ID) {
          channel->close();
          return;
        }

        current_id = PONG_ID;
        channel->write(make_dummy_packet(PONG_ID));
      });

      channel->on_error([&](const ChannelPtr& channel) { EXPECT_TRUE(false); });

      channel->on_close([&](const ChannelPtr& channel) { listener.stop(); });
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
      channel->on_read([&](const ChannelPtr& channel, const PacketPtr& pong) {
        EXPECT_EQ(PONG_ID, pong->get_id());

        channel->write(make_dummy_packet(PONG_ID));
      });

      channel->on_close([&](const ChannelPtr& channel) { client.stop(); });

      channel->write(make_dummy_packet(PING_ID));
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
                           const PacketPtr& message) {
        EXPECT_EQ(current_number, message->get_id());

        channel->write(make_dummy_packet(current_number));
        current_number++;
      });

      channel->on_close([&](const ChannelPtr& channel) { listener.stop(); });
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
                           const PacketPtr& message) {
        EXPECT_EQ(current_number, message->get_id());

        if (current_number == MAX_ID) {
          channel->close();
          return;
        }

        current_number++;
        channel->write(make_dummy_packet(current_number));
      });

      channel->on_error([&](const ChannelPtr& channel) { EXPECT_TRUE(false); });

      channel->on_close([&](const ChannelPtr& channel) { client.stop(); });

      channel->write(make_dummy_packet(current_number));
    });
    auto err = client.connect_to(HOST, PORT);
    EXPECT_EQ(CLOSED_ERR_CODE, err);
  });

  th_client.join();
  th_listener.join();
}

using simple::AnotherSimple;
using simple::Simple;
using simple::SimpleParent;
using simple::YetAnotherSimple;
using simple::YetYetAnotherSimple;

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
    container.add_a(AnotherSimple(10));
  }
  return container;
}

void check_yet_another_simple(const shared_ptr<const YetAnotherSimple>& pkt) {
  ASSERT_NE(nullptr, pkt);

  EXPECT_NE(0, pkt->get_s());
  EXPECT_EQ(size_t(pkt->get_s()), pkt->get_simples().size());

  for (auto& simple : pkt->get_simples()) {
    EXPECT_EQ(uint8_t(1), simple->get_x());
  }
}

void check_yetyet_another_simple(
    const shared_ptr<const YetYetAnotherSimple>& pkt) {
  ASSERT_NE(nullptr, pkt);

  EXPECT_NE(0, pkt->get_s());
  EXPECT_EQ(size_t(pkt->get_s() / 3), pkt->get_a().size());
}


TEST(ChannelIntegration, PingPongGeneratedPackets) {
  typedef shared_ptr<Channel<SimpleParent>> ChannelPtr;
  typedef shared_ptr<const SimpleParent> SimplePacketPtr;

  const int CLOSED_ERR_CODE = 1;
  const std::string HOST = "127.0.0.1";
  const int PORT = 22225;

  auto packet_factory = make_packet_factory<SimpleParent>();

  auto th_listener = std::thread([&]() {
    ChannelListener<SimpleParent> listener(packet_factory);
    listener.on_accept([&](const ChannelPtr& channel) {
      channel->on_read([&](const ChannelPtr& channel,
                           const SimplePacketPtr& pkt) {
        auto const y_simple = dynamic_pointer_cast<const YetAnotherSimple>(pkt);
        auto const yy_simple =
            dynamic_pointer_cast<const YetYetAnotherSimple>(pkt);

        auto is_pong = yy_simple != nullptr;

        if (is_pong) {
          check_yetyet_another_simple(yy_simple);
          channel->close();
          return;
        }

        check_yet_another_simple(y_simple);
        channel->write(make_yetyet_another_simple(2));
      });

      channel->on_error([&](const ChannelPtr& channel) { EXPECT_TRUE(false); });

      channel->on_close([&](const ChannelPtr& channel) { listener.stop(); });
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
                           const SimplePacketPtr& pkt) {
        auto const yy_simple =
            dynamic_pointer_cast<const YetYetAnotherSimple>(pkt);

        ASSERT_NE(nullptr, yy_simple);

        check_yetyet_another_simple(yy_simple);
        channel->write(make_yetyet_another_simple(2));
      });

      channel->on_close([&](const ChannelPtr& channel) { client.stop(); });

      channel->write(make_yet_another_simple(2));
    });
    auto err = client.connect_to(HOST, PORT);
    EXPECT_EQ(CLOSED_ERR_CODE, err);
  });

  th_client.join();
  th_listener.join();
}


}  // namespace packet

