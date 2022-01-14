
from PyQt5.QtCore import QObject, pyqtSignal, pyqtSlot
from data_structures import MMSettings
import nidaqmx
import nidaqmx.stream_writers
import numpy as np

import time
from event_thread import EventThread
from gui.GUIWidgets import SettingsView


class NIDAQ(QObject):

    new_ni_settings = pyqtSignal(MMSettings)

    def __init__(self, event_thread: EventThread, settings: MMSettings = MMSettings()):
        super().__init__()
        self.system = nidaqmx.system.System.local()

        self.sampling_rate = 500

        self.update_settings(settings)

        self.task = nidaqmx.Task()
        self.task.ao_channels.add_ao_voltage_chan('Dev1/ao0') # galvo channel
        self.galvo = Galvo(self)
        # self.task.ao_channels.add_ao_voltage_chan('Dev1/ao1') # z stage
        self.task.ao_channels.add_ao_voltage_chan('Dev1/ao2') # camera channel
        self.camera = Camera(self)
        self.task.ao_channels.add_ao_voltage_chan('Dev1/ao3') # aotf blanking channel
        self.task.ao_channels.add_ao_voltage_chan('Dev1/ao4') # aotf 488 channel
        self.task.ao_channels.add_ao_voltage_chan('Dev1/ao5') # aotf 561 channel
        self.aotf = AOTF(self)

        self.task.timing.cfg_samp_clk_timing(rate=self.smpl_rate,
                                sample_mode=nidaqmx.constants.AcquisitionType.FINITE,
                                samps_per_chan=100)
        self.stream = nidaqmx.stream_writers.AnalogMultiChannelWriter(self.task.out_stream,
                                                                      auto_start=True)

        self.acq = Acquisition(self, settings)

        self.event_thread = event_thread
        self.event_thread.acquisition_started_event.connect(self.run_acquisition_task)
        self.event_thread.mda_settings_event.connect(self.new_settings)

    def update_settings(self, new_settings):
        self.cycle_time = new_settings.channels['488']['exposure']
        self.sweeps_per_frame = settings.sweeps_per_frame
        self.frame_rate = 1/(self.cycle_time*self.sweeps_per_frame/1000)
        self.smpl_rate = round(self.sampling_rate*self.frame_rate*self.sweeps_per_frame*self.sweeps_per_frame)
        self.n_points = self.sampling_rate*self.sweeps_per_frame
        #settings for all pulses:
        self.duty_cycle = 10/self.n_points
        print('NI settings set')

    @pyqtSlot(MMSettings)
    def new_settings(self, new_settings: MMSettings):
        self.update_settings(new_settings)
        self.acq.update_settings(new_settings)
        print('NEW SETTINGS SET')

    @pyqtSlot(object)
    def run_acquisition_task(self, _):
        self.task.stop()
        print('Received ACQ STARTED EVT')
        time.sleep(0.5)
        self.acq.run_acquisition()




class Acquisition(QObject):

    def __init__(self, ni:NIDAQ, settings: MMSettings):
        super().__init__()
        self.settings = settings
        self.ni = ni
        self.daq_data = None
        self.ready = True
        self.make_daq_data()
        # self.ni.task.timing.cfg_samp_clk_timing(rate=self.ni.smpl_rate,
        #                         sample_mode=nidaqmx.constants.AcquisitionType.FINITE,
        #                         samps_per_chan=self.daq_data.shape[1])
        # # print('Stream length ', self.daq_data.shape[1])
        # self.ni.stream = nidaqmx.stream_writers.AnalogMultiChannelWriter(self.ni.task.out_stream,
        #                                                                  auto_start=True)

    def update_settings(self, new_settings):
        self.ready = False
        self.settings = new_settings
        self.make_daq_data()
        self.ni.task.timing.cfg_samp_clk_timing(rate=self.ni.smpl_rate,
                                sample_mode=nidaqmx.constants.AcquisitionType.FINITE,
                                samps_per_chan=self.daq_data.shape[1])
        print('Stream length ', self.daq_data.shape[1])
        self.ni.stream = nidaqmx.stream_writers.AnalogMultiChannelWriter(self.ni.task.out_stream,
                                                                         auto_start=True)
        self.ready = True

    def make_daq_data(self):
        timepoint = self.generate_one_timepoint()
        # print('timepoint_shape ', timepoint.shape)
        timepoint = self.add_interval(timepoint)
        self.daq_data = np.tile(timepoint, self.settings.timepoints)


    def generate_one_timepoint(self):
        channels_data = []
        for channel in self.settings.channels.values():
            # print(channel)
            if channel['use']:
                galvo = self.ni.galvo.one_frame(self.settings)
                camera = self.ni.camera.one_frame(self.settings)
                aotf = self.ni.aotf.one_frame(self.settings, channel)
                channel_data = np.vstack((galvo, camera, aotf))
                # print('channel shape   ', channel_data.shape)
                channels_data.append(channel_data)
        timepoint = np.hstack(channels_data)
        return timepoint

    def add_interval(self, timepoint):
        if (self.ni.smpl_rate*settings.interval_ms/1000 <= timepoint.shape[1] and
            settings.interval_ms > 0):
            print('Error: interval time shorter than time required to acquire single timepoint.')
            settings.interval_ms = 0

        if settings.interval_ms > 0:
            missing_samples = round(self.ni.smpl_rate * settings.interval_ms/1000-timepoint.shape[1])
            galvo = np.ones(missing_samples) * self.ni.galvo.parking_voltage
            rest = np.zeros((timepoint.shape[0] - 1, missing_samples))
            delay = np.vstack([galvo, rest])
            timepoint = np.hstack([timepoint, delay])
        return timepoint


    def run_acquisition(self):
        print("WRITING")
        written = self.ni.stream.write_many_sample(self.daq_data, timeout=20)
        print('================== Data written        ', written)


def make_pulse(ni, start, end, offset):
    up = np.ones(round(ni.duty_cycle*ni.n_points))*start
    down = np.ones(ni.n_points-round(ni.duty_cycle*ni.n_points))*end
    pulse = np.concatenate((up,down)) + offset
    return pulse


class Galvo:
    def __init__(self, ni: NIDAQ):
        self.ni = ni
        self.offset_0= -0.15
        self.amp_0 = 0.75
        self.parking_voltage = -3
        # self.ni.new_ni_settings.connect(self.register_settings)

    def one_frame(self, settings):
        self.n_points = self.ni.sampling_rate*settings.sweeps_per_frame
        down1 = np.linspace(0,-self.amp_0,round(self.n_points/(4*settings.sweeps_per_frame)))
        up = np.linspace(-self.amp_0,self.amp_0,round(self.n_points/(2*settings.sweeps_per_frame)))
        down2 = np.linspace(self.amp_0,0,round(self.n_points/settings.sweeps_per_frame) -
                            round(self.n_points/(4*settings.sweeps_per_frame)) -
                            round(self.n_points/(2*settings.sweeps_per_frame)))
        galvo_frame = np.concatenate((down1, up, down2))
        galvo_frame = np.tile(galvo_frame, settings.sweeps_per_frame)
        galvo_frame = galvo_frame + self.offset_0
        galvo_frame = galvo_frame[0:self.n_points]
        galvo_frame = self.add_delays(galvo_frame, settings)
        return galvo_frame

    def add_delays(self, frame, settings):
        if settings.post_delay > 0:
            delay = np.ones(round(self.ni.smpl_rate * settings.post_delay)) * self.parking_voltage
            frame = np.hstack([frame, delay])

        if settings.pre_delay > 0:
            delay = np.ones(round(self.ni.smpl_rate * settings.pre_delay)) * self.parking_voltage
            frame = np.hstack([delay, frame])

        return frame


class Camera:
    def __init__(self, ni: NIDAQ):
        self.ni = ni
        self.pulse_voltage = 5

    def one_frame(self, settings):
        camera_frame = make_pulse(self.ni, 5, 0, 0)
        camera_frame = self.add_delays(camera_frame, settings)
        return camera_frame

    def add_delays(self, frame, settings):
        if settings.post_delay > 0:
            delay = np.zeros(round(self.ni.smpl_rate * settings.post_delay))
            frame = np.hstack([frame, delay])

        if settings.pre_delay > 0:
            delay = np.zeros(round(self.ni.smpl_rate * settings.pre_delay))
            #TODO whty is predelay after camera trigger?
            # Maybe because the camera 'stores' the trigger?
            frame = np.hstack([frame, delay])

        return frame


class AOTF:
    def __init__(self, ni:NIDAQ):
        self.ni = ni
        self.blank_voltage = 10

    def one_frame(self, settings:MMSettings, channel:dict):
        blank = make_pulse(self.ni, 0, self.blank_voltage, 0)
        if channel['name'] == '488':
            aotf_488 = make_pulse(self.ni, 0, channel['power']/10, 0)
            aotf_561 = make_pulse(self.ni, 0, 0, 0)
        elif channel['name'] == '561':
            aotf_488 = make_pulse(self.ni, 0, 0, 0)
            aotf_561 = make_pulse(self.ni, 0, channel['power']/10, 0)
        aotf = np.vstack((blank, aotf_488, aotf_561))
        aotf = self.add_delays(aotf, settings)
        return aotf

    def add_delays(self, frame:np.ndarray, settings: MMSettings):
        if settings.post_delay > 0:
            delay = np.zeros((frame.shape[0], round(self.ni.smpl_rate * settings.post_delay)))
            frame = np.hstack([frame, delay])

        if settings.pre_delay > 0:
            delay = np.zeros((frame.shape[0], round(self.ni.smpl_rate * settings.pre_delay)))
            frame = np.hstack([delay, frame])

        return frame


if __name__ == '__main__':
    import sys
    from PyQt5 import QtWidgets
    app = QtWidgets.QApplication(sys.argv)

    channels = {'488': {'name':'488', 'use': True, 'exposure': 100, 'power': 10},
                '561': {'name':'561', 'use': True, 'exposure': 100, 'power':10}}
    settings = MMSettings(channels=channels, n_channels=2)
    event_thread = EventThread()
    event_thread.start()

    ni = NIDAQ(event_thread, settings)

    settings_view = SettingsView(event_thread)
    settings_view.show()

    sys.exit(app.exec_())
