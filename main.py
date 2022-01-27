from MicroManagerControl import MicroManagerControl
from data_structures import MMSettings
from gui.GUIWidgets import SettingsView
import sys
from PyQt5 import QtWidgets
from event_threadQ import EventThread
from gui.MainGUI import MainGUI
from hardware.nidaq import NIDAQ


def main():
    app = QtWidgets.QApplication(sys.argv)


    event_thread = EventThread()
    event_listener = event_thread.listener

    mm_interface = MicroManagerControl(event_listener)


    ni = NIDAQ(event_listener, mm_interface)
    settings_view = SettingsView(event_listener)
    miniapp = MainGUI(event_thread=event_listener)
    miniapp.show()


    sys.exit(app.exec_())



if __name__ == "__main__":
    main()
