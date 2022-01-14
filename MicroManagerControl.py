from PyQt5.QtWidgets import QWidget
from pycromanager import Bridge
from PyQt5.QtCore import QObject, QTimer, pyqtSlot
from PyQt5.QtGui import QImage

import numpy
import time
from qimage2ndarray import gray2qimage


class MicroManagerControl(QObject):

    def __init__(self):
        super().__init__()
        self.bridge = Bridge()
        self.studio = self.bridge.get_studio()
        self.data = self.studio.data
        self.core = self.bridge.get_core()
        self.image_format = QImage.Format.Format_Grayscale16
        self.LUT = []
        self.zPosition = self.core.get_position()
        self.move_to = self.zPosition

        self.z_update_timer = QTimer()
        self.z_update_timer.timeout.connect(self.update_z)
        self.z_update_timer.start(30)

    @pyqtSlot(object)
    def set_xy_position(self, pos: tuple):
        self.core.set_xy_position(pos[0], pos[1])

    @pyqtSlot(float)
    def track_z_change(self, pos: float):
        if self.move_to == self.zPosition:
            self.set_z_position(self.zPosition + pos)
        new_pos = self.move_to + pos
        if new_pos < 200 and new_pos > 0:
            self.move_to = self.move_to + pos

    def update_z(self):
        if self.zPosition is not self.move_to:
            self.set_z_position(self.move_to)
            self.zPosition = self.move_to

    @pyqtSlot(float)
    def set_z_position(self, pos: float):
        self.core.set_position(self.zPosition)
        print(self.move_to)

    def set_bit_depth(self):
        bit_depth = self.core.get_image_bit_depth
        if bit_depth == 8:
            self.image_format = QImage.Format.Format_Grayscale8
        elif bit_depth == 16:
            self.image_format = QImage.Format.Format_Grayscale16

    @pyqtSlot(object)
    def convert_image(self, image: numpy.ndarray, normalize: bool = True):
        # t1 = time.perf_counter()
        qimage = gray2qimage(image, normalize=normalize)
        # print(time.perf_counter() - t1)
        return qimage


if __name__ == '__main__':
    import gui.MainGUI as MainGUI
    MainGUI.main()
