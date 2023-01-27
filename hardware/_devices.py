from typing import Protocol, List
from pymm_eventserver.data_structures import MMSettings
import numpy as np
import nidaqmx
import nidaqmx.stream_writers
import matplotlib.pyplot as plt


class DAQSettings(Protocol):
    smapling_rate: int
    final_sample_rate: int


class DAQDevice(Protocol):
    """A device that can be controlled with data from an NIDAQ card."""

    def set_daq_settings(self, settings: DAQSettings) -> None:
        """Set sampling_rate and cycle time."""

    def one_frame(self, settings: DAQSettings) -> np.ndarray:
        """Return one frame that fits to the settings passed in."""

    def plot(self):
        """Plot the daq_data for one frame with matplotlib."""
        daq_data = self.one_frame(self.settings)
        x = np.divide(list(range(daq_data.shape[1])),self.settings.final_sample_rate/1000)
        for channel in range(daq_data.shape[0]):
            plt.step(x, daq_data[channel,:])


class NIController(Protocol):
    """A controller that wraps several DAQDevices and provides data to them"""
    daq_data: np.ndarray = np.zeros(())
    stream: nidaqmx.stream_writers.AnalogMultiChannelWriter = None
    task: nidaqmx.Task = None
    task_name: str = "generic"
    channels: List[str] = []
    settings: DAQSettings
    stop_task: bool = False

    def _init(self):
        try:
            self.task = nidaqmx.system.storage.persisted_task.PersistedTask(self.task_name).load()
        except nidaqmx.DaqError as e:
            print(f"Task not found error {e.error_code}, creating new one")
            self.task = nidaqmx.Task(self.task_name)
            for channel in self.channels:
                self.task.ao_channels.add_ao_voltage_chan(channel)
            self.task.save()
        print(self.task)
        self.setup(self.settings)

    def one_sequence(self) -> np.ndarray:
        raise NotImplementedError

    def setup(self, settings:DAQSettings) -> None:
        self.daq_data = self.one_sequence()
        self.task.timing.cfg_samp_clk_timing(rate=self.settings.final_sample_rate,
                                             sample_mode=nidaqmx.constants.AcquisitionType.CONTINUOUS,
                                             samps_per_chan=self.daq_data.shape[1])
        self.task.out_stream.regen_mode = nidaqmx.constants.RegenerationMode.DONT_ALLOW_REGENERATION
        self.stream = nidaqmx.stream_writers.AnalogMultiChannelWriter(self.task.out_stream,
                                                                         auto_start=False)
        self.stream.write_many_sample(self.daq_data)
        n_samples = 
        self.task.register_every_n_samples_transferred_from_buffer_event((self.daq_data.shape[1]),
                                                                            self.get_new_data)

    def get_new_data(self, task_handle, every_n_samples_event_type, number_of_samples, callback_data):
        if self.stop_task is True:
            self.stream.write_many_sample(self.stop_data)
            self.stop_task = 5
        elif self.stop_task == 5:
            self.task.stop()
            self.stream.write_many_sample(self.daq_data)
            self.stop_task = False
        else:
            self.stream.write_many_sample(self.daq_data)
        return 0

    def reload(self):
        self.daq_data = self.one_sequence()

    def stop(self):
        self.stop_task = True

    def start(self):
        self.task.start()

    def cleanup(self):
        self.task.close()
