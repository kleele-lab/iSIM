from pycromanager import Bridge
from PyQt5.QtCore import pyqtSlot
from PyQt5.QtGui import QImage
import MainGUI
import numpy
import time
from qimage2ndarray import gray2qimage

class MicroManagerControl():

    def __init__(self):
        self.bridge = Bridge()
        self.studio = self.bridge.get_studio()
        self.data = self.studio.data
        self.core = self.bridge.get_core()
        self.image_format = QImage.Format.Format_Grayscale16
        self.LUT = []


    @pyqtSlot(object)
    def set_xy_position(self, pos: tuple):
        self.core.set_xy_position(pos[0],pos[1])

    @pyqtSlot(float)
    def set_z_position(self, pos: float):
        self.core.set_position(pos)


    def set_bit_depth(self):
        bit_depth = self.core.get_image_bit_depth
        if bit_depth == 8:
            self.image_format = QImage.Format.Format_Grayscale8
        elif bit_depth == 16:
            self.image_format = QImage.Format.Format_Grayscale16

    @pyqtSlot(object)
    def convert_image(self, image: numpy.ndarray):
        t1 = time.perf_counter()
        qimage = gray2qimage(image, normalize=True)
        print(time.perf_counter() - t1)
        return qimage


if __name__ == '__main__':
    MainGUI.main()