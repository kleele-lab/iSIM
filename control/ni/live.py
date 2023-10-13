import numpy as np
from nidaqmx import Task as NITask
import nidaqmx
from pymmcore_plus import CMMCorePlus
from threading import Timer

CONTINUOUS = nidaqmx.constants.AcquisitionType.CONTINUOUS

class LiveEngine():
    def __init__(self, task: NITask = None, mmcore: CMMCorePlus = None):
        self._mmc = mmcore or CMMCorePlus.instance()

        if task is None:
            self.task = NITask()
            self.task.ao_channels.add_ao_voltage_chan('Dev1/ao2')
            self.task.ao_channels.add_ao_voltage_chan('Dev1/ao6')
            self.task.timing.cfg_samp_clk_timing(rate=400,
                                                 sample_mode=CONTINUOUS)
        else:
            self.task = task

        self._mmc.events.continuousSequenceAcquisitionStarted.connect(
            self._on_sequence_started
        )
        self._mmc.events.sequenceAcquisitionStopped.connect(self._on_sequence_stopped)

    def _on_sequence_started(self):
        self.task.start()
        self.timer = LiveTimer(0.2, self.task.write, args=(self.one_frame(),))
        self.timer.start()

    def _on_sequence_stopped(self):
        self.timer.cancel()
        self.task.write(np.array([[0], [0]]))
        self.task.stop()

    def one_frame(self):
        camera = np.hstack([np.ones(20)*5, np.zeros(10)])
        led = camera
        return np.vstack([camera, led])


class LiveTimer(Timer):
    def run(self):
        while not self.finished.wait(self.interval):
            self.function(*self.args, **self.kwargs)



if __name__ == "__main__":
    from qtpy.QtWidgets import QApplication
    from pymmcore_widgets import LiveButton, ImagePreview
    app = QApplication([])

    mmc = CMMCorePlus().instance()
    mmc.loadSystemConfiguration("C:/iSIM/Micro-Manager-2.0.2/prime_only.cfg")
    mmc.setCameraDevice("Prime")
    mmc.setProperty("Prime", "TriggerMode", "Edge Trigger")

    live_btn = LiveButton()
    image_prev = ImagePreview()
    image_prev.show()
    live_btn.show()

    engine = LiveEngine(mmcore=mmc)

    app.exec_()