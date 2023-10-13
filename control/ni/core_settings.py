from pymmcore_plus import CMMCorePlus
import useq
from gui.hardware.nidaq_components.devices import AOTF

class NISettings():
    def __init__(self, mmcore:CMMCorePlus = None):
        self.mmcore = mmcore or CMMCorePlus.instance()
        self.mmcore.mda.events.sequenceStarted.connect(self.on_sequence_start)

        self.aotf = AOTF()

    def on_sequence_start(self, event):
        readout = self.mmcore.getProperty("Prime", "Timing-ReadoutTimeNs")
        self.readout_time = float(readout)/1e9
