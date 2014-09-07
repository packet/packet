package packet

import (
	"net"
	"testing"
	"time"

	"../../../out/Debug/gen/packet/test/simple"
)

func testPktCtor(b []byte) (SizedBuffer, error) {
	p := simple.NewSimpleWithBuf(b)
	return &p, nil
}

func localListener(addr string, joinCh chan bool, t *testing.T) {
	defer func() {
		joinCh <- true
	}()

	l, err := net.Listen("tcp", addr)
	if err != nil {
		t.Fatal(err)
	}

	for {
		conn, err := l.Accept()
		if err != nil {
			return
		}

		go func(nc net.Conn) {
			pc := NewConn(nc, testPktCtor)
			pkts := make([]interface{}, 10)

			read := 0

			for read < 2 {
				n, err := pc.Read(pkts[read:])
				if err != nil {
					break
				}
				read += n
			}

			if read != 2 {
				t.Errorf("Conn read %d packets instead of 2 packets", read)
			}

			if err := pc.Write(pkts[0:2]); err != nil {
				t.Errorf("Cannot send packets: %v", err)
			}

			pc.Close()
			l.Close()
		}(conn)
	}
}

func connect(addr string, t *testing.T) {
	nc, err := net.Dial("tcp", addr)
	if err != nil {
		t.Fatal(err)
	}

	pc := simple.NewSimpleConn(nc)
	pkts := []simple.Simple{
		simple.NewSimple(),
		simple.NewSimple(),
	}

	if err := pc.WritePackets(pkts); err != nil {
		t.Fatal(err)
	}

	pkts[0].SetX(0)
	pkts[1].SetX(0)

	read := 0
	for read < 2 {
		n, err := pc.ReadPackets(pkts[read:])
		if err != nil {
			break
		}

		read += n
	}

	if read != 2 {
		t.Errorf("Cannot read %d packets instead of 2 packets", read)
	}

	if pkts[0].Size() != 1 || pkts[1].Size() != 1 {
		t.Errorf("Invalid packets received.")
	}

	pc.Close()
}

func TestConn(t *testing.T) {
	ch := make(chan bool)
	addr := "127.0.0.1:12345"
	go localListener(addr, ch, t)
	time.Sleep(1 * time.Second)
	connect(addr, t)
	<-ch
}
