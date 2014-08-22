// This package implements the basic runtime utilies for packets.
package packet

import "fmt"

type Packet struct {
	Buf []byte
}

// Returns the size of this packet. This method is always overriden by the real
// packets.
func (p *Packet) Size() int {
	return len(p.Buf)
}

func (p *Packet) OpenGap(offset, size int) {
	p_size := p.Size()
	if p_size < offset {
		panic(fmt.Sprintf("Offset (%d) is larger than the size (%d)", offset,
			p_size))
	}

	if cap(p.Buf) < offset+size {
		// This can result into a buffer with more than twice the requested size.
		b := make([]byte, len(p.Buf), cap(p.Buf)+(offset+size)*2)
		copy(b, p.Buf)
	}

	if len(p.Buf) < offset+size {
		p.Buf = p.Buf[:offset+size]
	}

	if p_size == offset {
		return
	}

	copy(p.Buf[offset:], p.Buf[offset+size:])
}

// Returns the size padded to the given multiple.
func PaddedSize(size int, multiple int) int {
	if multiple == 0 {
		return size
	}

	return ((size + multiple - 1) / multiple) * multiple
}
