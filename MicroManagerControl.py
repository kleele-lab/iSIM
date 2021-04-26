from pycromanager import Bridge
from PyQt5.QtCore import pyqtSlot


class MicroManagerControl():

    def __init__(self):
        self.bridge = Bridge()
        self.studio = self.bridge.get_studio()
        self.core = self.bridge.get_core()

    @pyqtSlot(object)
    def set_xy_position(self, pos: tuple):
        self.core.set_xy_position(pos[0],pos[1])

    @pyqtSlot(float)
    def set_z_position(self, pos: float):
        self.core.set_position(pos)