import useq
import numpy as np
import matplotlib.pyplot as plt
import time

from devices import AOTF, Camera, Galvo, Twitcher, Stage
from control.ni.core_settings import NISettings

class ISIMFrame():
    def __init__(self, settings:NISettings):

        self.galvo = Galvo()
        self.camera = Camera()
        self.aotf = AOTF()
        self.twitcher = Twitcher()
        self.stage = Stage()

        self.settings = settings
        self.settings.get_settings()

    def get_data(self, event: useq.MDAEvent, next_event: useq.MDAEvent|None = None):
        galvo = self.galvo.one_frame(self.settings)
        stage = self.stage.one_frame(self.settings, event, next_event)
        camera = self.camera.one_frame(self.settings)
        aotf = self.aotf.one_frame(event, self.settings)
        twitcher = self.twitcher.one_frame(self.settings)
        return np.vstack([galvo, stage, camera, aotf, twitcher])

    def plot(self):
        event = useq.MDAEvent(channel={"config": "488"}, z_pos=2)
        event2 = useq.MDAEvent(channel={"config": "488"}, z_pos=5)
        t0 = time.perf_counter()
        data = self.get_data(event, event2)
        print("Time to get data:", time.perf_counter() - t0)
        for device in data:
            plt.step(np.arange(len(device)), device)
        plt.show()


if __name__ == "__main__":
    from pymmcore_plus import CMMCorePlus
    mmc = CMMCorePlus()
    mmc.loadSystemConfiguration("C:/iSIM/Micro-Manager-2.0.2/prime_only.cfg")
    mmc.setCameraDevice("Prime")
    mmc.setExposure(100)
    mmc.setProperty("Prime", "TriggerMode", "Edge Trigger")
    settings = NISettings(mmc)
    event = useq.MDAEvent(channel={"config": "488"}, metadata={'power':50})
    event = useq.MDAEvent(channel={"config": "488"}, z_pos=2)
    event2 = useq.MDAEvent(channel={"config": "488"}, z_pos=5)
    frame = ISIMFrame(settings)
    data = frame.get_data(event)
    frame.plot()
