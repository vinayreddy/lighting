#!/usr/bin/python3

from absl import app
import DMXEnttecPro

from absl import flags
from DMXEnttecPro.utils import get_port_by_serial_number

flags.DEFINE_string("serial_number", "6A2VUCNP", "Serial number of the device")
flags.DEFINE_integer("baud_rate", 250000, "Baud rate for DMX")

FLAGS = flags.FLAGS

def setColor(dmx, startChannel, dim, r, g, b, w):
  dmx.set_channel(startChannel, dim)
  dmx.set_channel(startChannel+1, r)
  dmx.set_channel(startChannel+2, g)
  dmx.set_channel(startChannel+3, b)
  dmx.set_channel(startChannel+4, w)
  dmx.submit()

def main(_):
  serialPort = get_port_by_serial_number(FLAGS.serial_number)
  print("DMX Device Addr: %s" % serialPort)
  dmx = DMXEnttecPro.Controller(port_string=serialPort, baudrate=FLAGS.baud_rate)
  dmx.clear_channels()
  setColor(dmx, 1, 160, 0, 180, 180, 0)
  setColor(dmx, 16, 160, 0, 180, 180, 0)
  print("1=%d, 2=%d, 3=%d, 4=%d, 5=%d" % (dmx.get_channel(1), dmx.get_channel(2),
    dmx.get_channel(3), dmx.get_channel(4), dmx.get_channel(5)))
  print("16=%d, 17=%d, 18=%d, 19=%d, 20=%d" % (dmx.get_channel(16), dmx.get_channel(17),
    dmx.get_channel(18), dmx.get_channel(19), dmx.get_channel(20)))


if __name__ == "__main__":
  app.run(main)
