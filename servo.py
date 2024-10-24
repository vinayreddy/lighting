#!/usr/bin/env python

import time

from gpiozero.pins.pigpio import PiGPIOFactory
from gpiozero import AngularServo

class Servo:
  def __init__(self, gpioNum):
    self.servo = AngularServo(gpioNum, min_angle=-90, max_angle=90)

  #def setAngle(self, angle):
  #  duty_cycle = int(2.5 * 10000 + (angle / 18) * 10000)  # Convert angle to duty cycle (0-1000000)
  #  self.pwm.hardware_PWM(gpioNum, 50, duty_cycle)

  def rotateLoop(self, startAngle, endAngle):
    angle = startAngle
    angleDelta = 5
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

      self.servo.angle = angle
      if reachedEnd:
        time.sleep(4)
      else:
        time.sleep(0.2)
