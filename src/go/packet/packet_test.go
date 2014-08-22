package packet

import (
	"testing"

	"../../../out/Debug/gen/packet/test/including"
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

func TestPolymorphism(t *testing.T) {
	buf := []byte{2, 4, 1, 1, 1, 1}
	par := simple.NewSimpleParent(buf, false)
	if !including.IsIncluding(par) {
		t.Error("Simple parent should be converatble to including.")
	}

	inc, err := including.ConvertToIncluding(par)
	if err != nil {
		t.Error(err)
	}

	simples := inc.S()
	if len(simples) != 2 {
		t.Errorf("There is %d simples instead of 2.", len(simples))
	}

	for _, s := range simples {
		if s.Size() != 1 {
			t.Errorf("Size of a simple is %d instead of 1.", s.Size())
		}
	}
}

func TestReadArray(t *testing.T) {
	buf := []byte{2, 4, 1, 1, 1, 1}
	inc := including.NewAnotherIncluding(buf, false)
	if inc.Arr() != [2]uint8{1, 1} {
		t.Errorf("Array in the packet is not correctly loaded: %v", inc.Arr())
	}
}
