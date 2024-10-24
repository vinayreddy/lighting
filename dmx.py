#!/usr/bin/env python

import DMXEnttecPro
import numpy as np
import pyaudio
import threading
import time

from absl import app
from absl import flags
from contextlib import contextmanager
from scipy.fftpack import fft
from DMXEnttecPro.utils import get_port_by_serial_number
from ctypes import CFUNCTYPE, c_char_p, c_int, cdll

CHUNK = 1024
FORMAT = pyaudio.paInt16
CHANNELS = 1
RATE = 44100

ERROR_HANDLER_FUNC = CFUNCTYPE(None, c_char_p, c_int, c_char_p, c_int, c_char_p)
def py_error_handler(filename, line, function, err, fmt):
    pass
c_error_handler = ERROR_HANDLER_FUNC(py_error_handler)

@contextmanager
def noalsaerr():
  asound = cdll.LoadLibrary('libasound.so')
  asound.snd_lib_error_set_handler(c_error_handler)
  yield
  asound.snd_lib_error_set_handler(None)

class DmxController:
  def __init__(self, serialNumber, baudRate):
    serialPort = get_port_by_serial_number(serialNumber)
    print("DMX Device Addr: %s" % serialPort)
    self.dmx = DMXEnttecPro.Controller(port_string=serialPort, baudrate=baudRate)
    self.dmx.clear_channels()
    self.syncLightsToAudio = False
    self.lock = threading.Lock()

  # Start the lighting loop in a separate thread
  def startLightingLoop(self):
    threading.Thread(target=self.lightingLoop, daemon=True).start()

  def setLight(self, brightness, r, g, b):
    startChannel = 1
    r = max(0, min(r, 255))
    g = max(0, min(g, 255))
    b = max(0, min(b, 255))
    self.dmx.set_channel(startChannel, brightness)
    self.dmx.set_channel(startChannel+1, r)
    self.dmx.set_channel(startChannel+2, g)
    self.dmx.set_channel(startChannel+3, b)
    self.dmx.set_channel(startChannel+5, 0)
    self.dmx.submit()

  def lightingLoop(self):
    # Start with a basic slow color cycle.
    self.dmx.set_channel(6, 150)
    self.dmx.submit()
    while True:
      p = None
      stream = None
      while True:
        with self.lock:
          if not self.syncLightsToAudio:
            break
        if p is None:
          with noalsaerr():
            p = pyaudio.PyAudio()
          stream = p.open(format=FORMAT, channels=CHANNELS, rate=RATE, input=True, frames_per_buffer=CHUNK)
        volume, frequency = self.analyzeAudio(stream)
        brightness = int(min(volume * 2/ 100, 255))  # Adjust scaling as needed
        r, g, b = self.mapFrequencyToColor(frequency)
        self.setLight(brightness, r, g, b)

      if p is not None:
        print("Changing colors relatively fast")
        self.dmx.set_channel(6, 150)
        self.dmx.submit()
        stream.stop_stream()
        stream.close()
        p.terminate()
      time.sleep(0.1)
  

  def analyzeAudio(self, stream):
    data = np.frombuffer(stream.read(CHUNK), dtype=np.int16)
    fft_data = fft(data)
    volume = np.mean(np.abs(data))
    frequency = np.argmax(np.abs(fft_data))
    return volume, frequency

  def mapFrequencyToColor(self, freq):
    # Smooth color transition based on frequency
    if freq <= 8:
      # Red (255, 0, 0) to Purple (255, 0, 255)
      r = 255
      g = 0
      b = int((freq / 100) * 255)
    elif freq <= 100:
      # Purple (255, 0, 255) to Blue (0, 0, 255)
      r = int(255 * (1 - (freq - 100) / 900))
      g = 0
      b = 255
    elif freq <= 1000:
      # Blue (0, 0, 255) to Green (0, 255, 0)
      r = 0
      g = int(255 * ((freq - 1000) / 4000))
      b = int(255 * (1 - (freq - 1000) / 4000))
    else:
      # Green for frequencies above 5000
      r, g, b = 0, 255, 0
    return r, g, b

  ''' Returns False if already running. Otherwise, start sync and return True'''
  def syncLightToAudio(self):
    with self.lock:
      if self.syncLightsToAudio:
        return False
      self.syncLightsToAudio = True
      return True

  def stopLightToAudioSync(self):
    with self.lock:
      self.syncLightsToAudio = False


def setColor(dmx, startChannel, dim, r, g, b, w):
  dmx.set_channel(startChannel, dim)
  dmx.set_channel(startChannel+1, r)
  dmx.set_channel(startChannel+2, g)
  dmx.set_channel(startChannel+3, b)
  dmx.set_channel(startChannel+4, w)
  dmx.submit()

def main(_):
  serialPort = get_port_by_serial_number("001A1938056C")
  print("DMX Device Addr: %s" % serialPort)
  dmx = DMXEnttecPro.Controller(port_string=serialPort, baudrate=FLAGS.baud_rate)
  dmx.clear_channels()
  setColor(dmx, 1, 160, 0, 180, 180, 0)
  setColor(dmx, 16, 160, 0, 180, 180, 0)
  print("1=%d, 2=%d, 3=%d, 4=%d, 5=%d" % (dmx.get_channel(1), dmx.get_channel(2),
    dmx.get_channel(3), dmx.get_channel(4), dmx.get_channel(5)))
  print("16=%d, 17=%d, 18=%d, 19=%d, 20=%d" % (dmx.get_channel(16), dmx.get_channel(17),
    dmx.get_channel(18), dmx.get_channel(19), dmx.get_channel(20)))


#if __name__ == "__main__":
#  app.run(main)
