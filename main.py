# Pico Simon Says: 2024 Colin Luoma
#
# License: GPL
"""Pico Simon Says"""
import sys
import time
import utime
import machine
import uos
import random
from machine import Pin, PWM, Timer

"""
Button
handles debouncing and button led status
"""
class Button:
    DOWN = 0
    UP = 1

    EDGE_DOWN = 0
    EDGE_UP = 1
    EDGE_SAME = 2

    def __init__(self, pin, led_pin, timeout=25):
        self.pin = pin
        self.led_pin = led_pin
        self.timeout = timeout
        self.debounce_timer = Timer(-1)
        self.is_timeout = False
        self.cur_value = pin.value()
        self.last_value = self.cur_value

    def _start_debounce_timer(self):
        self.debounce_timer.init(period=self.timeout, mode=Timer.ONE_SHOT,
                                 callback=self._cancel_timeout)

    def _cancel_timeout(self, _):
        self.is_timeout = False

    def check_edge(self):
        self.cur_value = self.pin.value()

        if self.cur_value == self.DOWN:
            self.led_pin.value(1)
        else:
            self.led_pin.value(0)

        if self.cur_value == self.DOWN and self.last_value == self.UP and not self.is_timeout:
            self.is_timeout = True
            self._start_debounce_timer()
            self.last_value = self.cur_value
            return self.EDGE_DOWN
        elif self.cur_value == self.UP and self.last_value == self.DOWN and not self.is_timeout:
            self.is_timeout = True
            self._start_debounce_timer()
            self.last_value = self.cur_value
            return self.EDGE_UP
        else:
            self.last_value = self.cur_value
            return self.EDGE_SAME

    def value(self):
        self.cur_value = self.pin.value()

        if self.cur_value == self.DOWN:
            self.led_pin.value(1)
        else:
            self.led_pin.value(0)

        if self.cur_value == self.DOWN and self.last_value != self.DOWN and not self.is_timeout:
            self.is_timeout = True
            self._start_debounce_timer()
            self.last_value = self.cur_value
            return self.DOWN
        elif self.cur_value == self.UP and self.last_value != self.UP and not self.is_timeout:
            self.is_timeout = True
            self._start_debounce_timer()
            self.last_value = self.cur_value
            return self.UP
        else:
            self.last_value = self.cur_value
            return self.UP
    
    def trigger_up(self) -> bool:
        self.cur_value = self.pin.value()

        if self.cur_value == 0:
            self.led_pin.value(1)
        else:
            self.led_pin.value(0)

        if self.cur_value == self.UP and self.last_value != self.UP and not self.is_timeout:
            self.is_timeout = True
            self._start_debounce_timer()
            self.last_value = self.cur_value
            return True
        else:
            self.last_value = self.cur_value
            return False
    
    def raw_value(self):
        return self.pin.value()


class Mixer:
    def __init__(self, b1, b2, b3, b4):
        self.lineup = []
        self.b1 = b1
        self.b2 = b2
        self.b3 = b3
        self.b4 = b4
    
    def set_currect(self, c):
        if self.lineup.count(c) == 1:
            self.lineup.remove(c)
        self.lineup.append(c)


    def play(self):
        if self.b1.raw_value() == 1 and self.b2.raw_value() == 1 and self.b3.raw_value() == 1 and self.b4.raw_value() == 1:
            bequiet()
        else:
            is_on = False
            for x in reversed(self.lineup):
                if x == 1 and self.b1.raw_value() == Button.DOWN:
                    playtone(tones["A5"])
                    is_on = True
                    break
                elif x == 2 and self.b2.raw_value() == Button.DOWN:
                    playtone(tones["G5"])
                    is_on = True
                    break
                elif x == 3 and self.b3.raw_value() == Button.DOWN:
                    playtone(tones["E5"])
                    is_on = True
                    break
                elif x == 4 and self.b4.raw_value() == Button.DOWN:
                    playtone(tones["D5"])
                    is_on = True
                    break
            if not is_on:
                bequiet()
                

buzzer_pin = Pin(28)
buzzer = PWM(buzzer_pin)

tones = {"B0": 31,"C1": 33,"CS1": 35,"D1": 37,"DS1": 39,"E1": 41,"F1": 44,"FS1": 46,"G1": 49,"GS1": 52,"A1": 55,
         "AS1": 58,"B1": 62,"C2": 65,"CS2": 69,"D2": 73,"DS2": 78,"E2": 82,"F2": 87,"FS2": 93,"G2": 98,"GS2": 104,
         "A2": 110,"AS2": 117,"B2": 123,"C3": 131,"CS3": 139,"D3": 147,"DS3": 156,"E3": 165,"F3": 175,"FS3": 185,
         "G3": 196,"GS3": 208,"A3": 220,"AS3": 233,"B3": 247,"C4": 262,"CS4": 277,"D4": 294,"DS4": 311,"E4": 330,
         "F4": 349,"FS4": 370,"G4": 392,"GS4": 415,"A4": 440,"AS4": 466,"B4": 494,"C5": 523,"CS5": 554,"D5": 587,
         "DS5": 622,"E5": 659,"F5": 698,"FS5": 740,"G5": 784,"GS5": 831,"A5": 880,"AS5": 932,"B5": 988,"C6": 1047,
         "CS6": 1109,"D6": 1175,"DS6": 1245,"E6": 1319,"F6": 1397,"FS6": 1480,"G6": 1568,"GS6": 1661,"A6": 1760,
         "AS6": 1865,"B6": 1976,"C7": 2093,"CS7": 2217,"D7": 2349,"DS7": 2489,"E7": 2637,"F7": 2794,"FS7": 2960,
         "G7": 3136,"GS7": 3322,"A7": 3520,"AS7": 3729,"B7": 3951,"C8": 4186,"CS8": 4435,"D8": 4699,"DS8": 4978
         }

def playtone(frequency):
    buzzer.duty_u16(5000)
    buzzer.freq(frequency)

def bequiet():
    buzzer.duty_u16(0)

# Enum for current operation mode; OFFLINE will not use any wifi features
class Mode():
    ONLINE = 1
    OFFLINE = 2


# Globals
MODE = Mode.OFFLINE


# GPIO pin setup
button_led_1 = Pin(10, Pin.OUT)
button_led_2 = Pin(11, Pin.OUT)
button_led_3 = Pin(12, Pin.OUT)
button_led_4 = Pin(13, Pin.OUT)

button_1 = Button(Pin(6, Pin.IN, Pin.PULL_UP), button_led_1)
button_2 = Button(Pin(7, Pin.IN, Pin.PULL_UP), button_led_2)
button_3 = Button(Pin(8, Pin.IN, Pin.PULL_UP), button_led_3)
button_4 = Button(Pin(9, Pin.IN, Pin.PULL_UP), button_led_4)

mixer = Mixer(button_1, button_2, button_3, button_4)

def player_input_pattern(pattern) -> bool:

    for x in pattern:
        while True:
            is_done = False

            e = button_1.check_edge()
            if e == Button.EDGE_DOWN:
                mixer.set_currect(1)
                print("button 1 pressed")
            elif e == Button.EDGE_UP:
                print("button 1 up")
                if x == 1: break
                else:
                    bequiet()
                    return False
            
            e = button_2.check_edge()
            if e == Button.EDGE_DOWN:
                mixer.set_currect(2)
                print("button 2 pressed")
            elif e == Button.EDGE_UP:
                print("button 2 up")
                if x == 2: break
                else:
                    bequiet()
                    return False
            
            e = button_3.check_edge()
            if e == Button.EDGE_DOWN:
                mixer.set_currect(3)
                print("button 3 pressed")
            elif e == Button.EDGE_UP:
                print("button 3 up")
                if x == 3: break
                else:
                    bequiet()
                    return False
            
            e = button_4.check_edge()
            if e == Button.EDGE_DOWN:
                mixer.set_currect(4)
                print("button 4 pressed")
            elif e == Button.EDGE_UP:
                print("button 4 up")
                if x == 4: break
                else:
                    bequiet()
                    return False
            
            mixer.play()
    
    bequiet()
    return True


def play_pattern(pattern):
    sleep_time = 0.45
    for x in pattern:
        if x == 1:
            playtone(tones["A5"])
            button_led_1.value(1)
            time.sleep(sleep_time)
            bequiet()
            button_led_1.value(0)
        elif x == 2:
            playtone(tones["G5"])
            button_led_2.value(1)
            time.sleep(sleep_time)
            bequiet()
            button_led_2.value(0)
        elif x == 3:
            playtone(tones["E5"])
            button_led_3.value(1)
            time.sleep(sleep_time)
            bequiet()
            button_led_3.value(0)
        elif x == 4:
            playtone(tones["D5"])
            button_led_4.value(1)
            time.sleep(sleep_time)
            bequiet()
            button_led_4.value(0)
        
        time.sleep(0.3)

def play_fail():
    sleep_time = 0.45
    for x in range(4):
        playtone(tones["D5"])
        button_led_1.value(1)
        button_led_2.value(1)
        button_led_3.value(1)
        button_led_4.value(1)
        time.sleep(sleep_time)
        bequiet()
        button_led_1.value(0)
        button_led_2.value(0)
        button_led_3.value(0)
        button_led_4.value(0)
        
        time.sleep(0.3)


def playsong():
    mysong = ["E5","G5","A5","P","E5","G5","B5","A5","P","E5","G5","A5","P","G5","E5"]
    leds = [button_led_1, button_led_2, button_led_3, button_led_4]
    l = 0
    for i in range(len(mysong)):
        leds[l].value(1)

        if (mysong[i] == "P"):
            bequiet()
        else:
            playtone(tones[mysong[i]])
        time.sleep(0.3)

        for q in leds:
            q.value(0)
        l += 1
        l %= 4

    bequiet()
    time.sleep(2)

def get_difficulty(current_level):
    max_level = current_level
    button_down = False
    if button_1.raw_value() == 0:
        max_level = 5
        button_down = True
    if button_2.raw_value() == 0:
        max_level = 10
        button_down = True
    if button_3.raw_value() == 0:
        max_level = 15
        button_down = True
    if button_4.raw_value() == 0:
        max_level = 20
        button_down = True
    
    if button_down:
        return max_level
    else:
        return current_level

p = []
level = 0
max_level = get_difficulty(10)

while level < max_level:
    print(level)
    p.append(random.randint(1,4))
    play_pattern(p)
    if player_input_pattern(p):
        time.sleep(1.5)
        level += 1
        if level == max_level:
            playsong()
            p.clear()
            level = 0
    else:
        time.sleep(0.5)
        play_fail()
        time.sleep(1.5)
        max_level = get_difficulty(max_level)
        p.clear()
        level = 0
