from typing import Protocol
from pymm_eventserver.data_structures import MMSettings
import numpy as np


class DAQSettings(Protocol):
    smapling_rate: int


class DAQDevice(Protocol):
    """A device that can be controlled with data from an NIDAQ card."""

    def set_daq_settings(self, settings: DAQSettings) -> None:
        """Set sampling_rate and cycle time."""

    def one_frame(self, settings: MMSettings) -> np.ndarray:
        """Return one frame that fits to the settings passed in."""
