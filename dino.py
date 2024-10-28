#!/usr/bin/env python

import asyncio
from scipy.fftpack import fft
import threading

from absl import app
from absl import flags
from concurrent.futures import ThreadPoolExecutor
from dmx import DmxController
from mp3 import playMp3
from pprint import pprint
from uiprotect.api import ProtectApiClient
from uiprotect.data.devices import Camera
from uiprotect.data.websocket import WSAction

HOST = "192.168.1.1"
PORT = 443
USERNAME = "vinayreddy"
PASSWORD = "pfo4VS0%Sz11"

FLAGS = flags.FLAGS
flags.DEFINE_string("serial_number", "001A1938056C", "Serial number of the device")
flags.DEFINE_integer("baud_rate", 250000, "Baud rate for DMX")

# G4 Pro MAC: 70A7410F85AC
# G3 Instant MAC: D021F991060D

class UnifiEventReader:
  def __init__(self, dmxController):
    self.protect = None
    self.unsub = None
    self.dmxController = dmxController
    self.cooldown = False  # Add a cooldown flag
    self.cooldownSecs = 15
    self.soundFiles = [
      "/home/vinayreddy/DinoSounds/trex_1.mp3",
      "/home/vinayreddy/DinoSounds/trex_2.mp3",
      "/home/vinayreddy/DinoSounds/trex_3.mp3"
    ]
    self.growlFile = "/home/vinayreddy/DinoSounds/growl.mp3"
    self.curSoundIndex = 0  # Initialize index for round-robin
    self.dinoRoarRunning = False
    self.dinoGrowlRunning = False
    self.growlCooldown = False
    self.growlCooldownSecs = 10

  async def initialize(self):
    self.protect = ProtectApiClient(HOST, PORT, USERNAME, PASSWORD, verify_ssl=False)
    await self.protect.update()
    self.unsub = self.protect.subscribe_websocket(self.unifiCb)
    self.wsUnsub = self.protect.subscribe_websocket_state(self.wsStateCb)

  def unifiCb(self, event):
    if event.action != WSAction.UPDATE:
      return
    if not isinstance(event.new_obj, Camera):
      return
    cam = event.new_obj
    if cam.mac == "D021F991060D":  # G3 Instant
      if cam.is_motion_detected:
        if self.cooldown:
          print("In cooldown, ignoring motion event...")
          return
        # If the dino is in growl mode, starting a 2nd playMp3() will kill the first one.
        print("Motion detected. Triggering dino actions...")
        asyncio.create_task(self.dinoRoar())  # Schedule dinoActions asynchronously
    elif cam.mac == "70A7410F85AC":
      if self.cooldown:
        print("In cooldown, ignoring motion event...")
        return
      if cam.is_motion_detected:
        print("Motion detected on G4. Play growl")
        asyncio.create_task(self.dinoGrowl())
        asyncio.create_task(self.resetCooldown())  # Schedule cooldown reset

  async def dinoGrowl(self):
    if self.dinoRoarRunning or self.dinoGrowlRunning:
      print("Growl/Roar already running... Skipping growl")
      return
    if self.cooldown or self.growlCooldown:
      print("Growl/Roar cooldown active... Skipping growl")
      return
    self.dinoGrowlRunning = True
    self.dmxController.syncLightToAudio()
    await playMp3(fname=self.growlFile)
    self.dmxController.stopLightToAudioSync()
    self.dinoGrowlRunning = False
    self.growlCooldown = True
    asyncio.create_task(self.resetGrowlCooldown())

  async def dinoRoar(self):
    if self.dinoRoarRunning:
      print("Dino roar already running... Skipping dino sound")
      return
    print("Kicking off dino sound...")
    self.dinoRoarRunning = True
    self.dmxController.syncLightToAudio()
    await playMp3(fname=self.soundFiles[self.curSoundIndex])
    self.curSoundIndex = (self.curSoundIndex + 1) % len(self.soundFiles)
    self.dmxController.stopLightToAudioSync()
    self.dinoRoarRunning = False
    self.cooldown = True
    asyncio.create_task(self.resetCooldown())  # Schedule cooldown reset

  async def wsStateCb(self, state):
    self.wsUnsub()
    self.unsub()
    while True:
      try:
        await self.initialize()
        break
      except Exception as e:
        print(f"Error reconnecting: {e}")
        await asyncio.sleep(10)

  def printCameraNames(self):
    print("Camera names:")
    for camera in self.protect.bootstrap.cameras.values():
      print(f"- {camera.name} {camera.mac}")

  async def resetCooldown(self):
    await asyncio.sleep(self.cooldownSecs)
    self.cooldown = False  # Reset cooldown flag

  async def resetGrowlCooldown(self):
    await asyncio.sleep(self.growlCooldownSecs)
    self.growlCooldown = False  # Reset cooldown flag

async def main():
  print(f"Serial number: {FLAGS.serial_number}")
  threadPool = ThreadPoolExecutor(max_workers=4)
  asyncio.get_event_loop().set_default_executor(threadPool)

  dmxController = DmxController(FLAGS.serial_number, FLAGS.baud_rate)
  dmxController.startLightingLoop()
  reader = UnifiEventReader(dmxController)
  await reader.initialize()
  reader.printCameraNames()

  while True:
    await asyncio.sleep(60)

if __name__ == "__main__":
    app.run(lambda _: asyncio.run(main()))
