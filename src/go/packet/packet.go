// This package implements the basic runtime utilies for packets.
package packet

type Packet struct {
	Buf []byte
}

// Returns the size of this packet. This method is always overriden by the real
// packets.
func (p *Packet) Size() int {
	return len(p.Buf)
}

// Returns the size padded to the given multiple.
func PaddedSize(size int, multiple int) int {
	if multiple == 0 {
		return size
	}

	return ((size + multiple - 1) / multiple) * multiple
}
