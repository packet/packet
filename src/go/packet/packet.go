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

// OpenGap opens an space of "size" bytes in the packet buffer at the "offset".
func (p *Packet) OpenGap(offset, size int) {
	pSize := p.Size()
	if pSize < offset {
		panic(fmt.Sprintf("Offset (%d) is larger than the size (%d)", offset,
			pSize))
	}

	if cap(p.Buf) < pSize+size {
		// This can result into a buffer with more than twice the requested size.
		b := make([]byte, len(p.Buf), cap(p.Buf)+(pSize+size)*2)
		copy(b, p.Buf)
		p.Buf = b
	}

	if len(p.Buf) < offset+size {
		p.Buf = p.Buf[:offset+size]
	}

	if pSize == offset {
		return
	}

	copy(p.Buf[offset:], p.Buf[offset+size:])
}

// PaddedSize returns the size padded to the given multiple.
func PaddedSize(size int, multiple int) int {
	if multiple == 0 {
		return size
	}

	return ((size + multiple - 1) / multiple) * multiple
}
