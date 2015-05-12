package packet

import "fmt"

// SizedBuffer is a buffer that has a specific size. All packets are Sized.
type SizedBuffer interface {
	Size() int
	Buffer() []byte
}

// Packet is the parent structure of all packets.
type Packet struct {
	Buf []byte // The underlying buffer of the packet.
}

// Size returns the size of this packet. This method is always overriden by the
// real packets.
func (p *Packet) Size() int {
	return len(p.Buf)
}

// Buffer returns the underlying buffer of this packet.
func (p *Packet) Buffer() []byte {
	return p.Buf
}

// OpenGap opens an space of size bytes in the packet buffer at the offset.
// packetSize is actual size of the packet (not the length of the underlying
// buffer) and must be passed to the function.
func (p *Packet) OpenGap(offset, size, packetSize int) {
	if packetSize < offset {
		panic(fmt.Sprintf("Offset (%d) is larger than the size (%d)", offset,
			packetSize))
	}

	if cap(p.Buf) < packetSize+size {
		// This can result into a buffer with more than twice the requested size.
		b := make([]byte, len(p.Buf), cap(p.Buf)+(packetSize+size)*2)
		copy(b, p.Buf)
		p.Buf = b
	}

	if len(p.Buf) < offset+size {
		p.Buf = p.Buf[:offset+size]
	}

	if packetSize == offset {
		return
	}

	copy(p.Buf[offset:], p.Buf[offset+size:])
}

// PaddedSize returns the size padded to the given multiple.
func PaddedSize(size int, multiple int, constant int) int {
	if multiple == 0 {
		return size + constant
	}

	return ((size+multiple-1)/multiple)*multiple + constant
}
