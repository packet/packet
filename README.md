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
languages. That's why I started the Packet project for these Odd (but important
:P) applications.

# How can I use it?
TODO(soheil): Write this part.

