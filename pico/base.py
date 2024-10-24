import machine
import time

led = machine.Pin('LED', machine.Pin.OUT)

def ConnectToWifi(wlan, ssid, password):
    wlan.connect(ssid, password)
    maxWait = 20
    while maxWait > 0:
        if wlan.isconnected():
            print("Connected. IP:", wlan.ifconfig()[0])
            led.on()
            return True
        maxWait -= 1
        print('Waiting for connection...')
        time.sleep(0.5)
        led.toggle()

    print("Failed to connect")
    led.off()
    return False

def GetServoPin(gpioNum):
  servoPin = machine.PWM(machine.Pin(gpioNum))
  servoPin.freq(50)
  return servoPin

def SetServoAngle(servoPin, angle):
    duty = int(1630 + (angle/180) * (8191-1638))
    servoPin.duty_u16(duty)
