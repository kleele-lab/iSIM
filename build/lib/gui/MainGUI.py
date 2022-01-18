import MicroManagerControl
from PyQt5.QtCore import pyqtSlot, pyqtSignal, QTimer
from gui.GUIWidgets import LiveView, PositionHistory, FocusSlider, AlignmentWidget, RunningMean
from event_thread import EventThread
from MonogramCC import MonogramCC
from PyQt5 import QtWidgets, QtCore
import sys
import time
import numpy as np

# Adjust for different screen sizes
QtWidgets.QApplication.setAttribute(QtCore.Qt.HighDpiScaleFactorRoundingPolicy.PassThrough)

class MainGUI(QtWidgets.QWidget):
    """ Makes a mini App that shows of the capabilities of the Widgets implemented here """

    def __init__(self, parent=None, monogram:bool = True, event_thread = None):
        super(MainGUI, self).__init__(parent=parent)
        # self.position_history = PositionHistory()
        self.focus_slider = FocusSlider()
        # self.live_view = LiveView()
        # self.alignment_widget = AlignmentWidget()
        try:  # this makes sense only if Micro-Manager is running
            if event_thread == None:
                self.event_thread = EventThread()
                self.event_thread.start()
            else:
                self.event_thread = event_thread
            self.event_thread.xy_stage_position_changed_event.connect(self.set_xy_pos)
            self.event_thread.stage_position_changed_event.connect(self.set_z_pos)
            # self.event_thread.new_image_event.connect(self.set_image)
            self.event_thread.acquisition_started_event.connect(self.set_bit_depth)
            self.event_thread.settings_event.connect(self.handle_settings)
            self.event_thread.mda_settings_event.connect(self.handle_mda_settings)


            self.mm_interface = MicroManagerControl.MicroManagerControl(event_thread=self.event_thread)
            # self.position_history.xy_stage_position_python.connect(self.set_xy_position_python)
            self.focus_slider.z_stage_position_python.connect(self.set_z_position_python)
        except TimeoutError as error:
            print(error)
            print('No, will work as Test Widgets')

        try:
            # This makes sense only if the controller is connected
            if monogram:
                self.monogram = MonogramCC()
                self.focus_slider.connect_monogram(self.monogram)

        except OSError as error:
            print(error)

        self.setLayout(QtWidgets.QHBoxLayout())
        # self.layout().addWidget(self.position_history)
        self.layout().addWidget(self.focus_slider)
        # self.layout().addWidget(self.live_view)
        # self.layout().addWidget(self.alignment_widget)
        self.setStyleSheet("background-color:black;")

    @pyqtSlot(float)
    def set_z_pos(self, pos):
        self.focus_slider.setValue(int(np.round(pos)))

    @pyqtSlot(object)
    def set_xy_pos(self, pos):
        self.position_history.blockSignals(True)
        self.position_history.stage_pos[0] = pos[0]
        self.position_history.stage_pos[1] = pos[1]
        self.position_history.stage_moved(self.position_history.stage_pos)
        self.position_history.blockSignals(False)

    @pyqtSlot(object)
    def set_xy_position_python(self, pos):
        self.event_thread.blockSignals(True)
        self.mm_interface.set_xy_position(pos)
        time.sleep(0.01)
        self.event_thread.blockSignals(False)

    @pyqtSlot(float)
    def set_z_position_python(self, pos):
        self.event_thread.blockSignals(True)
        self.mm_interface.set_z_position(pos)
        self.event_thread.blockSignals(False)


    @pyqtSlot()
    def set_bit_depth(self):
        self.mm_interface.set_bit_depth()

    @pyqtSlot(object)
    def set_image(self, evt):
        image = evt.raw_image
        # image = image.get_raw_pixels().reshape([image.shape[0], image.shape[1]])
        self.live_view.set_qimage(self.mm_interface.convert_image(image))
        # self.alignment_widget.add_image(image)

    @pyqtSlot(str, str, str)
    def handle_settings(self, device, deviceProperty, value):
        print(deviceProperty)
        if device == "Dummy_488_Power" and deviceProperty == 'Power (% of max)':
            self.position_history.laser = float(value)
            print(self.position_history.laser)

    @pyqtSlot(object)
    def handle_mda_settings(self, settings):
        print(settings.root())

    def closeEvent(self, event):
        try:
            self.event_thread.stop()
        except AttributeError:
            # Event Thread was not added in the first place
            pass
        self.position_history.painter.end()
        event.accept()


class AlignmentGUI(QtWidgets.QWidget):
    """ Makes a mini App that shows of the capabilities of the Widgets implemented here """

    def __init__(self, parent=None, monogram:bool = True):
        super(AlignmentGUI, self).__init__(parent=parent)
        self.mean = RunningMean()
        self.view = AlignmentWidget()
        self.view.setFixedWidth(1800)
        try:  # this makes sense only if Micro-Manager is running
            self.event_thread = EventThread()
            self.event_thread.start()
            self.event_thread.new_image_event.connect(self.mean.add_image)
            self.event_thread.new_image_event.connect(self.view.add_image)
        except TimeoutError as error:
            print(error)
            print('No, will work as Test Widgets')

        self.setLayout(QtWidgets.QHBoxLayout())
        self.layout().addWidget(self.mean)
        self.layout().addWidget(self.view)
        self.setStyleSheet("background-color:black;")


def main():
    app = QtWidgets.QApplication(sys.argv)
    miniapp = MainGUI()
    miniapp.show()
    sys.exit(app.exec_())


if __name__ == '__main__':
    main()
