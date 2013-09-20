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
#include <thread>

#include "third_party/libuv/include/uv.h"

#include "gtest/gtest.h"

#include "packet/channel.h"
#include "packet/packet.h"

namespace packet {

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

typedef std::shared_ptr<Channel<DummyPacket>> ChannelPtr;
typedef std::shared_ptr<const DummyPacket> PacketPtr;

template <typename Channel>
void dispose_channel(const std::shared_ptr<Channel>& channel) {
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

  dummy_channel->on_read(
      [&](const ChannelPtr& channel, const PacketPtr& packet) {
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
  typedef std::shared_ptr<Channel<DummyPacket>> ChannelPtr;
  const int CLOSED_ERR_CODE = 1;
  const std::string HOST = "127.0.0.1";
  const int PORT = 22222;

  auto packet_factory = make_packet_factory<DummyPacket>();

  auto th_listener = std::thread([&] () {
        ChannelListener<DummyPacket> listener(packet_factory);
        listener.on_accept([&] (const ChannelPtr& channel) {
              channel->close();
              listener.stop();
            });
        auto err = listener.listen(HOST, PORT);
        EXPECT_EQ(CLOSED_ERR_CODE, err);
      });

  auto th_client = std::thread([&] () {
        std::chrono::milliseconds duration(2000);
        std::this_thread::sleep_for(duration);

        ChannelClient<DummyPacket> client(packet_factory);
        client.on_connect([&] (const ChannelPtr& channel) {
              channel->on_error([&](const ChannelPtr& channel) {
                    channel->close();
                    client.stop();
                  });
            });
        auto err = client.connect_to(HOST, PORT);
        EXPECT_EQ(CLOSED_ERR_CODE, err);
      });

  th_client.join();
  th_listener.join();
}

std::unique_ptr<DummyPacket> make_dummy_packet(uint8_t id) {
  std::unique_ptr<DummyPacket> p(new DummyPacket());
  p->set_size(DummyPacket::SIZE);
  p->set_id(id);
  return p;
}

TEST(ChannelIntegration, PingPong) {
  const int CLOSED_ERR_CODE = 1;
  const std::string HOST = "127.0.0.1";
  const int PORT = 22223;

  const uint8_t PING_ID = 1;
  const uint8_t PONG_ID = 2;

  auto packet_factory = make_packet_factory<DummyPacket>();

  auto th_listener = std::thread([&] () {
        uint8_t current_id = PING_ID;
        ChannelListener<DummyPacket> listener(packet_factory);
        listener.on_accept([&] (const ChannelPtr& channel) {
              channel->on_read(
                  [&] (const ChannelPtr& channel, const PacketPtr& ping) {
                    EXPECT_EQ(current_id, ping->get_id());

                    if (current_id == PONG_ID) {
                      channel->close();
                      return;
                    }

                    current_id = PONG_ID;
                    channel->write(make_dummy_packet(PONG_ID));
                  });

              channel->on_error([&] (const ChannelPtr& channel) {
                    EXPECT_TRUE(false);
                  });

              channel->on_close([&] (const ChannelPtr& channel) {
                    listener.stop();
                  });
            });
        auto err = listener.listen(HOST, PORT);
        EXPECT_EQ(CLOSED_ERR_CODE, err);
        if (err != CLOSED_ERR_CODE) {
          printf("Listener error: %s\n", uv_strerror(err));
        }
      });

  auto th_client = std::thread([&] () {
        std::chrono::milliseconds duration(2000);
        std::this_thread::sleep_for(duration);

        ChannelClient<DummyPacket> client(packet_factory);
        client.on_connect([&] (const ChannelPtr& channel) {
              channel->on_read(
                  [&](const ChannelPtr& channel, const PacketPtr& pong) {
                    EXPECT_EQ(PONG_ID, pong->get_id());

                    channel->write(make_dummy_packet(PONG_ID));
                  });

              channel->on_error([&](const ChannelPtr& channel) {
                    channel->close();
                  });

              channel->on_close([&] (const ChannelPtr& channel) {
                    client.stop();
                  });

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

  auto th_listener = std::thread([&] () {
        uint8_t current_number = 0;

        ChannelListener<DummyPacket> listener(packet_factory);
        listener.on_accept([&] (const ChannelPtr& channel) {
              channel->on_read(
                  [&] (const ChannelPtr& channel, const PacketPtr& message) {
                    EXPECT_EQ(current_number, message->get_id());

                    channel->write(make_dummy_packet(current_number));
                    current_number++;
                  });

              channel->on_error([&] (const ChannelPtr& channel) {
                    channel->close();
                  });

              channel->on_close([&] (const ChannelPtr& channel) {
                    listener.stop();
                  });
            });
        auto err = listener.listen(HOST, PORT);
        EXPECT_EQ(CLOSED_ERR_CODE, err);
        if (err != CLOSED_ERR_CODE) {
          printf("Listener error: %s\n", uv_strerror(err));
        }
      });

  auto th_client = std::thread([&] () {
        std::chrono::milliseconds duration(2000);
        std::this_thread::sleep_for(duration);

        uint8_t current_number = 0;

        ChannelClient<DummyPacket> client(packet_factory);
        client.on_connect([&] (const ChannelPtr& channel) {
              channel->on_read(
                  [&](const ChannelPtr& channel, const PacketPtr& message) {
                    EXPECT_EQ(current_number, message->get_id());

                    if (current_number == MAX_ID) {
                      channel->close();
                      return;
                    }

                    current_number++;
                    channel->write(make_dummy_packet(current_number));
                  });

              channel->on_error([&](const ChannelPtr& channel) {
                    EXPECT_TRUE(false);
                  });

              channel->on_close([&] (const ChannelPtr& channel) {
                    client.stop();
                  });

              channel->write(make_dummy_packet(current_number));
            });
        auto err = client.connect_to(HOST, PORT);
        EXPECT_EQ(CLOSED_ERR_CODE, err);
      });

  th_client.join();
  th_listener.join();
}

}  // namespace packet
