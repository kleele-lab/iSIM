from PyQt5.QtCore import QTimer
import nidaqmx
import numpy as np
import FilterFlipper



def aotf(transmit:bool = True):
    value = 10 if transmit else 0
    with nidaqmx.Task() as task:
        task.ao_channels.add_ao_voltage_chan("Dev1/ao3")
        task.ao_channels.add_ao_voltage_chan("Dev1/ao4")
        task.write([value,value], auto_start=True)


def center_mirror(pos:float = -0.15):
    with nidaqmx.Task() as task:
        task.ao_channels.add_ao_voltage_chan("Dev1/ao0")
        task.write(pos, auto_start=True)

def led_on(power=10):
    with nidaqmx.Task() as task:
        task.ao_channels.add_ao_voltage_chan("Dev1/ao6")
        task.write(power, auto_start=True)

def brightfield(on:bool = True):
    power = 0.3 if on else 0
    aotf(not on)
    led_on(power)
    FilterFlipper.brightfield(on)



def makePulse(start, end, offset):
    SamplingRate = 500
    SweepsPerFrame = 1
    noPoints = SamplingRate*SweepsPerFrame

    DutyCycle=10/noPoints
    up = np.ones(round(DutyCycle*noPoints))*start
    down = np.ones(noPoints-round(DutyCycle*noPoints))*end
    pulse = np.concatenate((up,down)) + offset
    return pulse