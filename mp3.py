#!/usr/bin/env python

import asyncio
import os
import subprocess

def blockingPlayMp3(fn: str, volume: int = 100) -> None:
    # Before playing, kill all other instances of ffplay
    os.system("pkill -f ffplay")
    
    # Use subprocess to run ffplay and capture output
    try:
        result = subprocess.run(
            ["ffplay", "-autoexit", "-nodisp", "-af", f"volume={volume/100.0}", fn],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            check=True
        )
    except subprocess.CalledProcessError as e:
        # Print stdout and stderr if an error occurs
        print("Error occurred while playing MP3:")
        print("stdout:", e.stdout)
        print("stderr:", e.stderr)

async def playMp3(fname, volume = 100):
  loop = asyncio.get_event_loop()
  await loop.run_in_executor(None, blockingPlayMp3, fname, volume)

# playMp3("/Users/vinayreddy/Desktop/DinoSounds/trex_1.mp3")
