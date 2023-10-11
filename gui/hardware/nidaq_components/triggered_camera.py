from pymmcore_plus import CMMCorePlus
from pymmcore_plus.mda import MDAEngine
from useq import MDAEvent, MDASequence
import nidaqmx
import numpy as np
import time
from threading import Thread
from datetime import datetime

mmc = CMMCorePlus()
mmc.loadSystemConfiguration("C:/iSIM/Micro-Manager-2.0.2/prime_only.cfg")

def makePulse(start, end, offset, n_points):
    DutyCycle=10/n_points
    up = np.ones(round(DutyCycle*n_points))*start
    down = np.ones(n_points-round(DutyCycle*n_points))*end
    pulse = np.concatenate((up,down)) + offset
    return pulse

class iSIMEngine(MDAEngine):
    def __init__(self, mmc):
        super().__init__(mmc)
        self.mmc = mmc
        self.task = nidaqmx.Task()
        self.task.ao_channels.add_ao_voltage_chan('Dev1/ao2')
        self.task2 = nidaqmx.Task()
        self.task2.ao_channels.add_ao_voltage_chan('Dev1/ao6')
        self.task.timing.cfg_samp_clk_timing(rate=9600, sample_mode=nidaqmx.constants.AcquisitionType.CONTINUOUS)
        self.task.start()
        self.task2.start()
        self.frame_times = []
        self.mmc.mda.events.frameReady.connect(self.on_frame)
        self.mmc.mda.events.sequenceFinished.connect(self.on_sequence_end)

    def setup_event(self, event):
        self.task2.write(5)
        return super().setup_event(event)

    def exec_event(self, event):
        try:
            thread = Thread(target=self.send_data)
            thread.start()
            self._mmc.snapImage()
            # self.task.write()
        except Exception as e:
            print("Could not snap")
            print(e)
            return ()
        return ((self._mmc.getImage(), event, self._mmc.getTags()),)

    def teardown_event(self, event: MDAEvent) -> None:
        self.task2.write(0)
        return super().teardown_event(event)

    def send_data(self):
        time.sleep(0.01)
        data = makePulse(5, 0, 0, 100)
        self.task.write(data)

    def on_frame(self, image, index, meta):
        time = datetime.strptime(meta["Time"], '%Y-%m-%d %H:%M:%S.%f')
        self.frame_times.append(time.timestamp()*1000)
        print(time.timestamp()*1000)

    def on_sequence_end(self):
        mean_offset = np.mean(np.diff(self.frame_times))
        std = np.std(np.diff(self.frame_times))
        print(mean_offset, std)


mmc.setExposure(100)
mmc.setCameraDevice("Prime")
mmc.setProperty("Prime", "TriggerMode", "Edge Trigger")


mmc.mda.set_engine(iSIMEngine(mmc))

sequence = MDASequence(
    time_plan={"interval": 1, "loops": 120},
)

mmc.run_mda(sequence)
