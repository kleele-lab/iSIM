from dataclasses import dataclass
import numpy as np


@dataclass
class PyImage:
    raw_image: np.ndarray
    timepoint: int
    channel: int
    time: int