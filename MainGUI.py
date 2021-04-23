from PyQt5.QtCore import pyqtSlot
from GUIWidgets import PositionHistory, FocusSlider
from EventThread import EventThread
from PyQt5 import QtWidgets
import sys



class MiniApp(QtWidgets.QWidget):
    """ Makes a mini App that shows of the capabilities of the Widgets implemented here """
    def __init__(self, parent = None):
        super(MiniApp, self).__init__(parent=parent)
        self.position_history = PositionHistory()
        self.focus_slider = FocusSlider()
        self.event_thread = EventThread()
        self.event_thread.run()
        self.event_thread.xy_stage_position_changed_event.connect(self.set_xy_pos)
        self.event_thread.stage_position_changed_event.connect(self.set_z_pos)

        self.setLayout(QtWidgets.QHBoxLayout())
        self.layout().addWidget(self.position_history)
        self.layout().addWidget(self.focus_slider)
        self.setStyleSheet("background-color:black;")

    def set_z_pos(self, pos):
        self.focus_slider.setValue(pos)

    def set_xy_pos(self, pos):
        self.position_history.stage_pos[0] = pos[0]
        self.position_history.stage_pos[1] = pos[1]
        self.position_history.stage_moved(self.position_history.stage_pos)


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
