
from sqlite3 import DataError
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
        self.settings = settings
        self.system = nidaqmx.system.System.local()

        self.sampling_rate = 500
        self.update_settings(self.settings)


        self.galvo = Galvo(self)
        self.stage = Stage(self)
        self.camera = Camera(self)
        self.aotf = AOTF(self)

        self.init_task()
        self.task.timing.cfg_samp_clk_timing(rate=self.smpl_rate,
                                sample_mode=nidaqmx.constants.AcquisitionType.FINITE,
                                samps_per_chan=100)
        self.stream = nidaqmx.stream_writers.AnalogMultiChannelWriter(self.task.out_stream,
                                                                      auto_start=True)

        self.acq = Acquisition(self, settings)
        self.live = LiveMode(self)

        self.event_thread = event_thread
        self.event_thread.live_mode_event.connect(self.start_live)
        self.event_thread.acquisition_started_event.connect(self.run_acquisition_task)
        self.event_thread.acquisition_ended_event.connect(self.acq_done)
        self.event_thread.mda_settings_event.connect(self.new_settings)
        self.event_thread.settings_event.connect(self.power_settings)

    def init_task(self):
        try: self.task.close()
        except: print("Task close failed")
        self.task = nidaqmx.Task()
        self.task.ao_channels.add_ao_voltage_chan('Dev1/ao0') # galvo channel
        self.task.ao_channels.add_ao_voltage_chan('Dev1/ao1') # z stage
        self.task.ao_channels.add_ao_voltage_chan('Dev1/ao2') # camera channel
        self.task.ao_channels.add_ao_voltage_chan('Dev1/ao3') # aotf blanking channel
        self.task.ao_channels.add_ao_voltage_chan('Dev1/ao4') # aotf 488 channel
        self.task.ao_channels.add_ao_voltage_chan('Dev1/ao5') # aotf 561 channel

    def update_settings(self, new_settings):
        self.cycle_time = new_settings.channels['488']['exposure']
        self.sweeps_per_frame = new_settings.sweeps_per_frame
        self.frame_rate = 1/(self.cycle_time*self.sweeps_per_frame/1000)
        self.smpl_rate = round(self.sampling_rate*self.frame_rate*self.sweeps_per_frame*self.sweeps_per_frame)
        self.n_points = self.sampling_rate*self.sweeps_per_frame
        #settings for all pulses:
        self.duty_cycle = 10/self.n_points
        print('NI settings set')

    @pyqtSlot(MMSettings)
    def new_settings(self, new_settings: MMSettings):
        self.settings = new_settings
        self.update_settings(new_settings)
        self.acq.update_settings(new_settings)
        print('NEW SETTINGS SET')

    @pyqtSlot(str, str, str)
    def power_settings(self, device, property, value):
        if device == "488_AOTF":
            self.settings.channels['488']['power'] = float(value)/10
            self.aotf.power_488 = float(value)/10
        elif device == "561_AOTF":
            self.settings.channels['561']['power'] = float(value)/10
            self.aotf.power_561 = float(value)/10
        print(self.settings.channels)

    @pyqtSlot(object)
    def run_acquisition_task(self, _):
        self.event_thread.mda_settings_event.disconnect(self.new_settings)
        print('Received ACQ STARTED EVT')
        time.sleep(0.5)
        self.acq.run_acquisition()

    @pyqtSlot(object)
    def acq_done(self, _):
        self.event_thread.mda_settings_event.connect(self.new_settings)
        time.sleep(1)
        self.task.stop()

    def generate_one_timepoint(self, live_channel: int = None):
        galvo = self.galvo.one_frame(self.settings)
        stage = self.stage.one_frame(self.settings)
        camera = self.camera.one_frame(self.settings)


        if not self.settings.use_channels or live_channel is not None:
            channel_number = 0 if live_channel is None else live_channel
            aotf = self.aotf.one_frame(self.settings,
                                       list(self.settings.channels.values())[channel_number])
            timepoint = np.vstack((galvo, stage, camera, aotf))
        else:
            channels_data = []
            for channel in self.settings.channels.values():
                if channel['use']:
                    aotf = self.aotf.one_frame(self.settings, channel)
                    channel_data = np.vstack((galvo, stage, camera, aotf))
                    channels_data.append(channel_data)
            timepoint = np.hstack(channels_data)
        return timepoint

    def start_live(self, live_is_on):
        self.live.toggle(live_is_on)

class LiveMode(QObject):
    def __init__(self, ni:NIDAQ):
        super().__init__()
        self.ni = ni
        self.make_daq_data()
        self.stop = False

    def update_settings(self, new_settings):
        self.ni.init_task()
        self.ni.task.timing.cfg_samp_clk_timing(rate=self.ni.smpl_rate,
                                             sample_mode=nidaqmx.constants.AcquisitionType.CONTINUOUS,
                                             samps_per_chan=self.daq_data.shape[1])
        self.ni.task.out_stream.regen_mode = nidaqmx.constants.RegenerationMode.DONT_ALLOW_REGENERATION
        self.ni.stream = nidaqmx.stream_writers.AnalogMultiChannelWriter(self.ni.task.out_stream,
                                                                         auto_start=False)
        self.ni.stream.write_many_sample(self.daq_data)
        self.ni.task.register_every_n_samples_transferred_from_buffer_event(2, self.get_new_data)

    def get_new_data(self, task_handle, every_n_samples_event_type, number_of_samples, callback_data):
        print('NEW DATA', time.perf_counter())
        if self.stop:
            self.stop = False
            print("STOP")
            self.ni.stream.write_many_sample(self.stop_data)
            print("STOPPING")
            self.ni.task.stop()
            self.ni.task.close()
        else:
            self.ni.stream.write_many_sample(self.daq_data)
        return 0

    def make_daq_data(self):
        timepoint = self.ni.generate_one_timepoint(0)
        no_frames = np.max([1, round(200/self.ni.cycle_time)])
        self.daq_data = np.tile(timepoint, no_frames)
        stop_data = np.asarray(
                [[self.ni.galvo.parking_voltage, 0, 0, 0, 0, 0]]).astype(np.float64).transpose()
        self.stop_data = np.tile(stop_data, self.daq_data.shape[1])
        print(self.daq_data.shape[1])

    def toggle(self, live_is_on):
        if live_is_on:
            self.stop = False
            self.update_settings(self.ni.settings)
            self.ni.task.start()
            print("STARTED", time.perf_counter())
        else:
            self.stop = True
            # time.sleep(1)
            # self.ni.task.stop()






class Acquisition(QObject):

    def __init__(self, ni:NIDAQ, settings: MMSettings):
        super().__init__()
        self.settings = settings
        self.ni = ni
        self.daq_data = None
        self.ready = True
        self.make_daq_data()

    def update_settings(self, new_settings):
        self.ready = False
        self.settings = new_settings
        self.make_daq_data()
        self.ni.init_task()
        self.ni.task.timing.cfg_samp_clk_timing(rate=self.ni.smpl_rate,
                                sample_mode=nidaqmx.constants.AcquisitionType.FINITE,
                                samps_per_chan=self.daq_data.shape[1])
        self.ni.stream = nidaqmx.stream_writers.AnalogMultiChannelWriter(self.ni.task.out_stream,
                                                                         auto_start=False)
        print('Stream length ', self.daq_data.shape[1])

        self.ready = True

    def make_daq_data(self):
        timepoint = self.ni.generate_one_timepoint()
        # print('timepoint_shape ', timepoint.shape)
        timepoint = self.add_interval(timepoint)
        self.daq_data = np.tile(timepoint, self.settings.timepoints)

    def add_interval(self, timepoint):
        if (self.ni.smpl_rate*self.settings.interval_ms/1000 <= timepoint.shape[1] and
            self.settings.interval_ms > 0):
            print('Error: interval time shorter than time required to acquire single timepoint.')
            self.settings.interval_ms = 0

        if self.settings.interval_ms > 0:
            missing_samples = round(self.ni.smpl_rate * self.settings.interval_ms/1000-timepoint.shape[1])
            galvo = np.ones(missing_samples) * self.ni.galvo.parking_voltage
            rest = np.zeros((timepoint.shape[0] - 1, missing_samples))
            delay = np.vstack([galvo, rest])
            timepoint = np.hstack([timepoint, delay])
        print("INTERVAL: ", self.settings.interval_ms)
        return timepoint

    def run_acquisition(self):
        self.update_settings(self.settings)
        print("WRITING, ", self.daq_data.shape)
        written = self.ni.stream.write_many_sample(self.daq_data, timeout=20)
        self.ni.task.start()
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


class Stage:
    #TODO: This was copied from the Camera, make adjustments for the stage!
    def __init__(self, ni: NIDAQ):
        self.ni = ni
        self.pulse_voltage = 5

    def one_frame(self, settings):
        stage_frame = make_pulse(self.ni, 5, 0, 0)
        stage_frame = np.zeros_like(stage_frame)
        stage_frame = self.add_delays(stage_frame, settings)
        return stage_frame

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
        self.power_488 = 10
        self.power_561 = 10

    def one_frame(self, settings:MMSettings, channel:dict):
        blank = make_pulse(self.ni, 0, self.blank_voltage, 0)
        if channel['name'] == '488':
            try: power = channel['power']/10
            except: power = self.power_488
            aotf_488 = make_pulse(self.ni, 0, power, 0)
            aotf_561 = make_pulse(self.ni, 0, 0, 0)
        elif channel['name'] == '561':
            try: power = channel['power']/10
            except: power = self.power_561
            aotf_488 = make_pulse(self.ni, 0, 0, 0)
            aotf_561 = make_pulse(self.ni, 0, power, 0)
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
