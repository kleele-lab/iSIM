from dataclasses import dataclass, field
import numpy as np
from typing import List, Any
from pathlib import Path


@dataclass
class PyImage:
    raw_image: np.ndarray
    timepoint: int
    channel: int
    time: int


@dataclass
class MMChannel:
    name: str
    active: bool
    power: float
    exposure_ms: int

@dataclass
class MMSettings:
    java_settings: Any = None

    timepoints: int =  11
    interval_ms: int = 1000

    pre_delay: float = 0.0
    post_delay: float = 0.03

    java_channels: Any = None
    use_channels = True
    channels: List[MMChannel] = None
    n_channels: int = 0

    slices_start: float = None
    slices_end: float = None
    slices_step: float = None

    save_path: Path = None
    prefix: str = None

    sweeps_per_frame: int = 1

    acq_order: str = None


    def __post_init__(self):

        if self.java_settings is not None:
            # print(dir(self.java_settings))
            self.interval_ms = self.java_settings.interval_ms()
            self.timepoints = self.java_settings.num_frames()
            self.java_channels = self.java_settings.channels()
            self.acq_order = self.java_settings.acq_order_mode()
            self.use_channels = self.java_settings.use_channels()

        try:
            self.java_channels.size()
        except:
            return

        self.channels = {}
        self.n_channels = 0
        for channel_ind in range(self.java_channels.size()):
            channel = self.java_channels.get(channel_ind)
            config = channel.config()
            self.channels[config] = {'name': config,
                                     'use': channel.use_channel(),
                                     'exposure': channel.exposure(),
                                     'z_stack': channel.do_z_stack(),
                                     'power': 10}
            if self.channels[config]['use']:
                self.n_channels += 1
