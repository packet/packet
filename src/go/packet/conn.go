package packet

import (
	"fmt"
	"net"
)

const (
	DefaultBufSize = 1 << 12
)

// Conn is a simple wrapper around net.Conn that can read and write packets.
type Conn struct {
	net.Conn
	ctor   Constructor
	buf    []byte
	offset int
}

// Constructor is a function that reads a packet from the buffer.
type Constructor func(b []byte) (SizedBuffer, error)

// NewConn creates a new connection that.wrapps c and parses packets using f.
func NewConn(c net.Conn, f Constructor) Conn {
	return Conn{
		Conn: c,
		ctor: f,
		buf:  make([]byte, DefaultBufSize),
	}
}

// Write serializes packets into the connection.
func (c *Conn) Write(pkts []interface{}) error {
	for _, p := range pkts {
		pkt, ok := p.(SizedBuffer)
		if !ok {
			return fmt.Errorf("%#v is not a sized buffer", p)
		}
		s := pkt.Size()
		b := pkt.Buffer()[:s]
		n := 0
		for s > 0 {
			var err error
			if n, err = c.Conn.Write(b); err != nil {
				return fmt.Errorf("Error in write: %v", err)
			}
			s -= n
		}
	}
	return nil
}

// Read reads packets from the connection.
func (c *Conn) Read(pkts []interface{}) (int, error) {
	if len(c.buf) == c.offset {
		newSize := DefaultBufSize
		if DefaultBufSize < len(c.buf) {
			newSize = 2 * len(c.buf)
		}

		buf := make([]byte, newSize)
		copy(buf, c.buf[:c.offset])
		c.buf = buf
	}

	r, err := c.Conn.Read(c.buf[c.offset:])
	if err != nil {
		return 0, err
	}

	r += c.offset

	s := 0
	n := 0
	for i := range pkts {
		p, err := c.ctor(c.buf)
		if err != nil {
			break
		}

		pSize := p.Size()
		if r < s+pSize {
			break
		}

		pkts[i] = p
		s += pSize
		n++
	}

	c.offset = r - s
	if c.offset < 0 {
		panic("Invalid value for offset")
	}

	c.buf = c.buf[s:]
	if c.offset < len(c.buf) {
		return n, nil
	}

	buf := make([]byte, DefaultBufSize)
	copy(buf, c.buf[:c.offset])
	c.buf = buf
	return n, nil
}
