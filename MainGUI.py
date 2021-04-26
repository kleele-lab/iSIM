from MicroManagerControl import MicroManagerControl
from PyQt5.QtCore import pyqtSlot, pyqtSignal
from GUIWidgets import PositionHistory, FocusSlider
from EventThread import EventThread
from PyQt5 import QtWidgets
import sys
import time
import numpy as np

class MiniApp(QtWidgets.QWidget):
    """ Makes a mini App that shows of the capabilities of the Widgets implemented here """

    def __init__(self, parent = None):
        super(MiniApp, self).__init__(parent=parent)
        self.position_history = PositionHistory()
        self.focus_slider = FocusSlider()
        self.event_thread = EventThread()
        self.mm_interface = MicroManagerControl()

        self.event_thread.start()
        self.event_thread.xy_stage_position_changed_event.connect(self.set_xy_pos)
        self.event_thread.stage_position_changed_event.connect(self.set_z_pos)

        self.position_history.xy_stage_position_python.connect(self.set_xy_position_python)
        self.focus_slider.z_stage_position_python.connect(self.set_z_position_python)


        self.setLayout(QtWidgets.QHBoxLayout())
        self.layout().addWidget(self.position_history)
        self.layout().addWidget(self.focus_slider)
        self.setStyleSheet("background-color:black;")

    @pyqtSlot(float)
    def set_z_pos(self, pos):
        self.focus_slider.setValue(int(np.round(pos)))

    @pyqtSlot(object)
    def set_xy_pos(self, pos):
        print('RECEIVED XY SIGNAL')
        self.position_history.blockSignals(True)
        self.position_history.stage_pos[0] = pos[0]
        self.position_history.stage_pos[1] = pos[1]
        self.position_history.stage_moved(self.position_history.stage_pos)
        self.position_history.blockSignals(False)

    @pyqtSlot(object)
    def set_xy_position_python(self, pos):
        self.event_thread.blockSignals(True)
        self.mm_interface.set_xy_position(pos)
        time.sleep(0.1)
        #Without the wait if it changes to fast it breaks the pycromanager socket
        self.event_thread.blockSignals(False)

    @pyqtSlot(float)
    def set_z_position_python(self, pos):
        self.event_thread.blockSignals(True)
        self.mm_interface.set_z_position(pos)
        time.sleep(0.07)
        #Without the wait if it changes to fast it breaks the pycromanager socket
        self.event_thread.blockSignals(False)

    def closeEvent(self, event):
        self.event_thread.stop()
        event.accept()


if __name__ == '__main__':
    import time
    app = QtWidgets.QApplication(sys.argv)
    # widget = FocusSlider()
    # widget = PositionHistory()
    # widget.stage_moved([70,100])
    # widget.stage_moved([-300,-100])
    # widget.show()
    miniapp = MiniApp()
    miniapp.show()
    sys.exit(app.exec_())
