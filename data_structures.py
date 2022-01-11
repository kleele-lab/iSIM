from dataclasses import dataclass
import numpy as np
from typing import List
from os.path import Path

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
    timepoints: int
    interval_ms: int

    channels: List[MMChannel]

    slices_start: float
    slices_end: float
    slices_step: float

    save_path: Path
    prefix: str