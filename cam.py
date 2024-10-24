#!/usr/bin/env python
#!/Users/vinayreddy/python/env_3.13/bin/python

import asyncio

from absl import app
from pprint import pprint
from uiprotect.api import ProtectApiClient
from uiprotect.data.devices import Camera
from uiprotect.data.websocket import WSAction

HOST = "192.168.1.1"
PORT = 443
USERNAME = "vinayreddy"
PASSWORD = "pfo4VS0%Sz11"

# MAC: 70A7410F85AC

class UnifiEventReader:
  def __init__(self):
    self.protect = None
    self.unsub = None

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
    if cam.mac != "70A7410F85AC":
      return
    if cam.is_motion_detected:
      print("Motion detected")
    if cam.is_smart_detected:
      print("Smart detected")
    if (not cam.is_motion_detected) and (not cam.is_smart_detected):
      return
    print(event)

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

async def main():
  reader = UnifiEventReader()
  await reader.initialize()
  reader.printCameraNames()

  while True:
    await asyncio.sleep(60)

if __name__ == "__main__":
    app.run(lambda _: asyncio.run(main()))
