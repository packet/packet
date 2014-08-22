package packet

import (
	"testing"

	"../../../out/Debug/gen/packet/test/simple"
)

func TestSimplePacket(t *testing.T) {
	buf := make([]byte, 100)
	pkt := simple.NewSimple(buf, false)
	if pkt.Size() != 0 {
		t.Errorf("Size of this simple must be 0 instead of %d.", pkt.Size())
	}

	pkt.SetX(1)
	if pkt.X() != 1 {
		t.Errorf("X of this simple packet is set to 1 not %d.", pkt.X())
	}

	if pkt.Size() != 1 {
		t.Errorf("Size of this simple must be 1 instead of %d.", pkt.Size())
	}
}
