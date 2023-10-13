from isimgui.hardware._devices import DAQDevice
from core_settings import NISettings
import numpy as np
from scipy import ndimage
import matplotlib.pyplot as plt
from typing import Union
import useq


def makePulse(start, end, offset, n_points):
    DutyCycle=10/n_points
    up = np.ones(round(DutyCycle*n_points))*start
    down = np.ones(n_points-round(DutyCycle*n_points))*end
    pulse = np.concatenate((up,down)) + offset
    return pulse


class Galvo(DAQDevice):
    """Galvo mirror, here for iSIM scanning"""
    def __init__(self):
        self.offset = -0.075  # -0.15
        self.amp = 0.2346  # 0.2346
        self.parking_voltage = self.offset  # -3.2

    def one_frame(self, settings: NISettings) -> np.ndarray:
        #TODO: Sweeps per frame not possible anymore!
        readout_length = settings.readout_points
        n_points = settings.real_exposure_points

        galvo_frame = np.linspace(-self.amp, self.amp, n_points)
        overshoot_points = int(np.ceil(round(readout_length/20)/2))
        scan_increment = galvo_frame[-1] - galvo_frame[-2]
        self.overshoot_amp =  scan_increment * (overshoot_points + 1)
        overshoot_0 = np.linspace(-self.amp - self.overshoot_amp, -self.amp - scan_increment,
                                  overshoot_points)
        overshoot_1 = np.linspace(self.amp + scan_increment, self.amp + self.overshoot_amp,
                                  overshoot_points)
        galvo_frame = np.hstack((overshoot_0, galvo_frame, overshoot_1)) + self.offset
        galvo_frame = self.add_readout(galvo_frame, settings)
        return galvo_frame

    def add_readout(self, frame, settings: NISettings):
        readout_length = settings.readout_points
        readout_length = readout_length - int(np.ceil(round(readout_length/20)/2))
        readout_delay0 = np.linspace(self.offset, -self.amp+self.offset-self.overshoot_amp,
                                     int(np.floor(readout_length*0.9)))
        readout_delay0 = np.hstack([readout_delay0,
                                    np.ones(int(np.ceil(readout_length*0.1)))*readout_delay0[-1]])
        readout_delay1 = np.linspace(self.offset + self.amp + self.overshoot_amp, self.offset,
                                     readout_length)
        return np.hstack([readout_delay0, frame, readout_delay1])

    def plot(self):
        daq_data = self.one_frame(self.settings)
        x = np.divide(list(range(len(daq_data))),self.settings.final_sample_rate/1000)
        plt.step(x, daq_data)


class Camera(DAQDevice):
        def __init__(self):
            self.pulse_voltage = 5

        def one_frame(self, settings: NISettings) -> np.ndarray:
            camera_frame = makePulse(self.pulse_voltage, 0, 0, settings.real_exposure_points)
            camera_frame = self.add_readout(camera_frame, settings)
            return camera_frame

        def add_readout(self, frame, settings):
            readout_delay = np.zeros(settings.readout_points)
            return np.hstack([frame, readout_delay, readout_delay])

        def plot(self):
            daq_data = self.one_frame(self.settings)
            x = np.divide(list(range(len(daq_data))),self.settings.final_sample_rate/1000)
            plt.step(x, daq_data)


class Twitcher(DAQDevice):
    def __init__(self):
        self.amp = 0.07
        # The sampling rate in the settings should divide nicely with the frequency
        self.freq = 2400  # Full cycle Hz
        self.offset = 5

    def one_frame(self, settings: NISettings) -> np.ndarray:
        #TODO: Think if the twitchers couldn't just run continously
        # This might be nice, because it might be a second task that runs at a higher frequency
        # if that's possible

        n_points = settings.total_points
        frame_time =  settings.camera_exposure_time # seconds
        wavelength = 1/self.freq  # seconds
        n_waves = frame_time/wavelength
        points_per_wave = int(np.ceil(n_points/n_waves))
        up = np.linspace(-1, 1, points_per_wave//2 + 1)
        down = np.linspace(1, -1, points_per_wave//2 + 1)
        frame = np.hstack((down[:-1], np.tile(np.hstack((up[:-1], down[:-1])), round(n_waves + 20)), up[:-1]))
        frame = ndimage.gaussian_filter1d(frame, points_per_wave/20)
        frame = frame[points_per_wave//2:n_points + points_per_wave//2]
        frame = frame*(self.amp/frame.max()) + self.offset
        frame = np.hstack([np.ones(settings.readout_points//2)*frame[-1],
                           frame,
                           np.ones(settings.readout_points//2)*frame[-1]])
        # frame = self.add_delays(frame, settings)
        # frame = np.expand_dims(frame, 0)
        return frame

    def plot(self):
        daq_data = self.one_frame(self.settings)
        x = np.divide(list(range(daq_data.shape[1])), self.settings.final_sample_rate/1000)
        plt.step(x, daq_data[0, :])


# class LED(DAQDevice):
    # def __init__(self, settings:NIDAQSettings = NIDAQSettings()):
    #     self.settings = settings
    #     self.blank_voltage = 10
    #     self.power = 2
    #     self.speed_adjustment = 0.98
    #     self.adjusted_readout = self.settings.camera_readout_time * self.speed_adjustment

    # def one_frame(self, settings: Union[NIDAQSettings, None] = None, power = None) -> np.ndarray:
    #     if power is not None:
    #         self.power = power
    #     if settings is not None:
    #         self.settings = settings
    #         self.adjusted_readout = self.settings.camera_readout_time * self.speed_adjustment
    #     n_shift = (round(self.settings.camera_readout_time * self.settings.final_sample_rate) -
    #                round(self.settings.final_sample_rate * self.adjusted_readout))
    #     n_points = (self.settings.n_points -
    #                 round(self.adjusted_readout * self.settings.final_sample_rate))
    #     led = np.ones(n_points) * self.power
    #     led = np.expand_dims(led, 0)
    #     led = self.add_readout(led)
    #     return led

    # def add_readout(self, frame:np.ndarray) -> np.ndarray:
    #     n_shift = (round(self.settings.camera_readout_time * self.settings.final_sample_rate) -
    #                round(self.settings.final_sample_rate * self.adjusted_readout))
    #     print("LED readout")
    #     print(n_shift)
    #     readout_delay0 = np.zeros((frame.shape[0],
    #                                round(self.settings.final_sample_rate * self.settings.camera_readout_time) - n_shift))
    #     readout_delay1 = np.zeros((frame.shape[0],
    #                                round(self.settings.final_sample_rate * self.settings.camera_readout_time)))
    #     frame = np.hstack([readout_delay0, frame, readout_delay1])
    #     return frame


class AOTF(DAQDevice):
    def __init__(self):
        self.blank_voltage = 10
        self.power_488 = 100
        self.power_561 = 100

    def one_frame(self, event:useq.MDAEvent, settings: NISettings) -> np.ndarray:
        n_points = settings.real_exposure_points

        blank = np.ones(n_points) * self.blank_voltage
        if event.channel.config == '488':
            aotf_488 = np.ones(n_points) * self.power_488/10
            aotf_561 = np.zeros(n_points)
        elif event.channel.config == '561':
            aotf_488 = np.zeros(n_points)
            aotf_561 = np.ones(n_points) * self.power_561/10
        elif event.channel.config == 'LED':
            aotf_488 = np.zeros(n_points)
            aotf_561 = np.zeros(n_points)
        aotf = np.vstack((blank, aotf_488, aotf_561))
        aotf = self.add_readout(aotf, settings)
        return aotf

    def add_readout(self, frame, settings):
        readout_delay = np.zeros((frame.shape[0], settings.readout_points))
        frame = np.hstack([readout_delay, frame,  readout_delay])
        return frame


class Stage(DAQDevice):
    def __init__(self):
        self.pulse_voltage = 5
        self.calibration = 202.161
        self.max_v = 10

    def one_frame(self, settings: NISettings, event: useq.MDAEvent,
                  next_event: useq.MDAEvent|None = None) -> np.ndarray:
        height_offset = event.z_pos or 0
        height_offset = self.convert_z(height_offset)
        stage_frame = np.ones(settings.readout_points + settings.real_exposure_points)*height_offset
        stage_frame = self.add_readout(stage_frame, settings, next_event)
        # stage_frame = self.add_delays(stage_frame, settings)
        return stage_frame

    def convert_z(self, z_um):
        return (z_um/self.calibration) * self.max_v

    def add_readout(self, frame, settings:NISettings, next_event:useq.MDAEvent|None):
        if next_event is None or next_event.z_pos is None:
            height_offset = frame[-1]
        else:
            height_offset = next_event.z_pos
        print("HEIGHT OFFSET", height_offset)
        readout_delay = np.ones(settings.readout_points)*self.convert_z(height_offset)
        frame = np.hstack([frame, readout_delay])
        return frame


def main():
    pass

if __name__ == "__main__":
    main()