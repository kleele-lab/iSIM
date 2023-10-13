import useq

from gui.hardware.nidaq_components.devices import AOTF
from control.ni.core_settings import NISettings


class NIFrame():
    def __init__(self):
        self.aotf = AOTF()
        self.settings = NISettings()

    def get_data(self, event: useq.MDAEvent):
        self.aotf.one_frame(self.settings, {'name': event.channel.config})
