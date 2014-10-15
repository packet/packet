# What's Packet?
Packet is a binary serialization framework, similar to
[Google Protocol Buffers](http://code.google.com/p/protobuf/),
[Apache Thrift](http://thrift.apache.org/), and
[MessagePack](http://msgpack.org/). Packets offers granular control over
underlying serialization format that enables you to define existing binary
formats (such as network protocols) and generate binding for them in your
favorite programming language.

# Are you crazy? Why do we need another binary serialization format?
Well, there are many binary protocols around: IP, TCP, and OpenFlow! Can you
define an OpenFlow packet in protocol buffers or thrift? No, because you don't
have control over the actual representation format. Their approach is elegant
for most applications, but won't work for predefined binary wire protocols.
If someone gives you a protocol definition in
[TLV](http://en.wikipedia.org/wiki/Type-length-value), you're on your own to
write the bindings. It gets even worse, when you have to support different
languages. That's why I started the Packet project for these Odd (but important) applications.

# Features
## Polymorphism
Packet support polymorphism as long as all the packets in the hierarchy are
generated in the same generation pass. The behaviour is undefined when Packets
are separately generated.

# Example
This is a packet snippet that implements an OpenFlow packet_in:

```
# Packet received on port (datapath -> controller).
@type_selector(type = Type.PT_PACKET_IN)
packet PacketIn(Header10) {
  uint32 buffer_id;     # ID assigned by datapath.
  uint16 total_len;     # Full length of frame.
  uint16 in_port;       # Port on which frame was received.
  uint8 reason;         # Reason packet is being sent (one of.PR_*)
  uint8 pad;

  @repeated
  uint8 data;           # Ethernet frame, halfway through 32-bit word,
                        # so the IP header is 32-bit aligned.  The
                        # amount of data is inferred from the length
                        # field in the header.  Because of padding,
                        # offsetof(packet PacketIn, data) ==
                        # sizeof(packet PacketIn) - 2.
}
```

`PacketIn` derives from openflow header v1.0. The type field of a packet in always is always PT_PACKET_IN.
