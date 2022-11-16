from hardware._devices import DAQDevice
from hardware.nidaq_components.settings import NIDAQSettings
import numpy as np
import matplotlib.pyplot as plt

def makePulse(start, end, offset, settings):
    DutyCycle=10/settings.n_points
    up = np.ones(round(DutyCycle*settings.n_points))*start
    down = np.ones(settings.n_points-round(DutyCycle*settings.n_points))*end
    pulse = np.concatenate((up,down)) + offset
    return pulse


class Galvo(DAQDevice):
    """Galvo mirror, here for iSIM scanning"""
    def __init__(self):
        self.amp_0 = 0.265
        self.offset_0= -0.3
        self.sampling_rate = None
        self.parking_voltage = self.offset_0

    def set_daq_settings(self, settings: NIDAQSettings) -> None:
        self.settings = settings

    def one_frame(self, settings: NIDAQSettings = NIDAQSettings()) -> np.ndarray:
        #TODO: Sweeps per frame not possible anymore!
        self.settings = settings
        # Make this 30 ms shorter for the camera readout
        n_points = settings.n_points - round(settings.camera_readout_time * settings.final_sample_rate)
        galvo_frame = np.linspace(-self.amp_0, self.amp_0, n_points) + self.offset_0
        # Add the 10 ms in the waiting position
        readout_delay0 = np.ones(round(settings.final_sample_rate * settings.camera_readout_time)) *\
                         (-self.amp_0 + self.offset_0)
        readout_delay1 = np.ones(round(settings.final_sample_rate * settings.camera_readout_time)) *\
                         (self.amp_0 + self.offset_0)
        galvo_frame = np.hstack([readout_delay0, galvo_frame, readout_delay1])
        galvo_frame = self.add_delays(galvo_frame, settings)
        return galvo_frame

    def add_delays(self, frame, settings):
        if settings.post_delay > 0:
            delay = (np.ones(round(settings.final_sample_rate * settings.post_delay)) *
                self.parking_voltage)
            frame = np.hstack([frame, delay])
        if settings.pre_delay > 0:
            delay = (np.ones(round(settings.final_sample_rate * settings.pre_delay)) *
                     self.parking_voltage)
            frame = np.hstack([delay, frame])
        return frame


    def plot(self):
        plt.plot(self.one_frame(self.settings))



class Camera(DAQDevice):
        def __init__(self):
            self.pulse_voltage = 5

        def one_frame(self, settings:NIDAQSettings) -> np.ndarray:
            self.settings = settings
            camera_frame = makePulse(self.pulse_voltage, 0, 0, settings)
            camera_frame = self.add_readout(camera_frame)
            camera_frame = self.add_delays(camera_frame)
            return camera_frame

        def add_delays(self, frame, pre_delay = 0, post_delay=0):
            if post_delay > 0:
                delay = np.zeros(round(self.settings.smpl_rate * self.settings.post_delay))
                frame = np.hstack([frame, delay])
            if pre_delay > 0:
                delay = np.zeros(round(self.settings.smpl_rate * self.settings.pre_delay))
                frame = np.hstack([delay, frame])
            return frame

        def add_readout(self, frame):
            # readout_time = self.core.get_property("PrimeB_Camera", "Timing-ReadoutTimeNs")
            # readout_time = float(readout_time)*1E-9  # in seconds
            # readout_time = 0.03
            readout_delay = np.zeros(round(self.settings.final_sample_rate * self.settings.camera_readout_time))
            return np.hstack([frame, readout_delay])

        def plot(self):
            plt.plot(self.one_frame(self.settings))