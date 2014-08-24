package packet

import (
	"testing"

	"../../../out/Debug/gen/packet/test/including"
	"../../../out/Debug/gen/packet/test/simple"
)

func TestSimplePacket(t *testing.T) {
	buf := make([]byte, 100)
	pkt := simple.NewSimpleWithBuf(buf)
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
	par := simple.NewSimpleParentWithBuf(buf)
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

func TestReadConstSizeArray(t *testing.T) {
	buf := []byte{2, 4, 1, 1, 1, 1}
	inc := including.NewAnotherIncludingWithBuf(buf)
	if inc.Arr() != [2]uint8{1, 1} {
		t.Errorf("Array in the packet is not correctly loaded: %v", inc.Arr())
	}
}

func TestWriteConstSizeArray(t *testing.T) {
	inc := including.NewAnotherIncluding()
	size := inc.Size()
	inc.SetArr([2]uint8{1, 1})
	if inc.Arr() != [2]uint8{1, 1} {
		t.Errorf("Array in the packet is not correctly loaded: %v", inc.Arr())
	}

	if inc.Size() != size {
		t.Errorf("Packet's size is modified after setting a const-sized array.")
	}
}

func TestReadCountedArray(t *testing.T) {
	buf := []byte{2, 6, 2, 1, 1, 2}
	pkt := simple.NewYetAnotherSimpleWithBuf(buf)
	if pkt.S() != 2 {
		t.Errorf("S is %d instead of 1.", pkt.S())
	}
	arr := pkt.Simples()
	if len(arr) != 2 {
		t.Errorf("Array does not have two elements: %v", arr)
	}

	if arr[0].X() != 1 || arr[1].X() != 1 {
		t.Errorf("Array is not correctly loaded: %v", arr)
	}
}

func TestWriteCountedArray(t *testing.T) {
	pkt := simple.NewYetAnotherSimple()
	if pkt.Size() != 4 {
		t.Errorf("Packet has a size of %d instead of 4.", pkt.Size())
	}

	pkt.AddSimples(simple.NewSimple())
	if len(pkt.Simples()) != 1 {
		t.Errorf("Counted array is not correctly added: %v", pkt.Simples())
	}

	pkt.AddSimples(simple.NewSimple())
	if len(pkt.Simples()) != 2 {
		t.Errorf("Counted array is not correctly added: %v", pkt.Simples())
	}

	if pkt.Size() != 6 {
		t.Errorf("Packet size is not updated after we add two elements.")
	}
}

func TestReadSizedArray(t *testing.T) {
	buf := []byte{3, 12, 9, 1, 3, 1, 1, 3, 1, 1, 3, 1}
	pkt := simple.NewYetYetAnotherSimpleWithBuf(buf)
	arr := pkt.A()
	if len(arr) != 3 {
		t.Errorf("Array is not correctly loaded: %v", arr)
	}

	for _, e := range arr {
		if e.Size() != 3 {
			t.Errorf("Array elements are not correcly loaded: %v", e)
		}
	}
}

func TestWriteSizedArray(t *testing.T) {
	pkt := simple.NewYetYetAnotherSimple()
	size := pkt.Size()

	pkt.AddA(simple.NewAnotherSimple())
	if len(pkt.A()) != 1 {
		t.Errorf("Array is not correctly added to the packet: %v", pkt.A())
	}

	pkt.AddA(simple.NewAnotherSimple())
	if len(pkt.A()) != 2 {
		t.Errorf("Array is not correctly added to the packet: %v", pkt.A())
	}

	if size == pkt.Size() {
		t.Errorf("Packet size is not updated after adding entries to the array.")
	}
}

func TestBigEndian(t *testing.T) {
	buf := []byte{0, 1}
	pkt := including.NewBigEndianPacketWithBuf(buf)
	if pkt.A() != 1 {
		t.Errorf("The big-endian field is %d instead of 1.", pkt.A())
	}

	pkt.SetA(0x100)
	if pkt.Buf[0] != 1 || pkt.Buf[1] != 0 {
		t.Errorf("The big endian field is set to %d instead of 0x100.", pkt.A())
	}
}

func TestPadded(t *testing.T) {
	padded := simple.NewPadded()
	if padded.Size() != 8 {
		t.Errorf("Padded's size is not padded to 8: %v.", padded.Size())
	}

	if padded.Len() != 8 {
		t.Errorf("Padded's size field is not padded to 8: %v.", padded.Len())
	}

	paddex := simple.NewPaddedExcluded()
	if paddex.Size() != 8 {
		t.Errorf("Paddex's size is not padded to 8: %v.", padded.Size())
	}

	if paddex.Len() != 1 {
		t.Errorf("Paddex's size field is padded to 8: %v.", padded.Len())
	}

	pkt := simple.NewPaddedIncluder()
	if pkt.Size() != 1 {
		t.Errorf("Padded includer's size is incorrect: %v.", pkt.Size())
	}

	pkt.SetPadded(padded)

	padded = pkt.Padded()
	if padded.Len() != 8 {
		t.Errorf("Padded length field is not updated: %v.", padded.Len())
	}

	if pkt.Size() != 9 {
		t.Errorf(
			"Packet's size is not correctly updated after added the padded field: %v",
			pkt.Size())
	}

	pkt.SetPaddedExcluded(paddex)

	paddex = pkt.PaddedExcluded()
	if paddex.Len() != 1 {
		t.Errorf("Padded excluded's size is incorrect: %v", paddex.Len())
	}

	if pkt.Size() != 17 {
		t.Errorf(
			"Packet's size is not correctly updated after added the padded field: %v",
			pkt.Size())
	}
}
