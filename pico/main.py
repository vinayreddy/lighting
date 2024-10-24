from base import *
from config import config

import network
import sys
import time
from machine import Pin, PWM
from neopixel import Neopixel

WS2812_GPIO_PIN = 14
SERVO_GPIO_PIN = 15
servoPin = PWM(Pin(SERVO_GPIO_PIN))
servoPin.freq(50)

def setAngle(angle):
    duty = int(1630 + (angle/180) * (8191-1638))
    servoPin.duty_u16(duty)

sys.path.append('.')
wlan = network.WLAN(network.STA_IF)
wlan.active(True)

#if ConnectToWifi(wlan, config['ssid'], config['password']):
#  print("Connected to WiFi")
#else:
#  raise RuntimeError("Failed to connect to WiFi")

def rotateLoop(startAngle, endAngle):
    angle = startAngle
    angleDelta = 2
    forward = True
    while True:
        reachedEnd = False
        if forward:
            angle += angleDelta
        else:
            angle -= angleDelta

        if angle >= endAngle:
            angle = endAngle
            forward = False
            reachedEnd = True
        elif angle <= startAngle:
            angle = startAngle
            forward = True
            reachedEnd = True
        setAngle(angle)
        foo = '''if not reachedEnd:
            if forward:
                setAngle(angle-2)
            else:
                setAngle(angle+2)
        else:
            if forward:
                setAngle(angle+2)
            else:
                setAngle(angle - 2)
        '''
        if reachedEnd:
            time.sleep(4)
        else:
            time.sleep(0.1)

numPixels = 128
pixels = Neopixel(numPixels, 0, WS2812_GPIO_PIN, "RGB")

def maybeRemapColor(rgb):
    if config['convertToGRB']:
        r, g, b = rgb
        return (g, r, b)
    else:
        return rgb

yellow = maybeRemapColor((255, 100, 0))
orange = maybeRemapColor((255, 50, 0))
green = maybeRemapColor((0, 255, 0))
blue = maybeRemapColor((0, 0, 255))
red = maybeRemapColor((255, 0, 0))
black = (0, 0, 0)


# Angle 0, dino is away from the door. Angle 25 it touches the glass.
#setAngle(10)
rotateLoop(0, 25)



foo = '''
color0 = red
pixels.brightness(50)
pixels.fill(orange)
pixels.set_pixel_line_gradient(3, 32, green, blue)
pixels.set_pixel(20, (255, 255, 255))

pixels.fill(black)
pixels.show()


while True:
    if color0 == red:
        color0 = yellow
        color1 = red
    else:
        color0 = red
        color1 = yellow
    pixels.set_pixel(0, color0)
    pixels.set_pixel(1, color1)
    pixels.show()
    time.sleep(1)
'''
