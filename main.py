from data_structures import MMSettings
from gui.GUIWidgets import SettingsView
import sys
from PyQt5 import QtWidgets
from event_thread import EventThread
from gui.MainGUI import MainGUI
from hardware.nidaq import NIDAQ


def main():
    app = QtWidgets.QApplication(sys.argv)

    channels = {'488': {'name':'488', 'use': True, 'exposure': 100, 'power': 10},
                '561': {'name':'561', 'use': True, 'exposure': 100, 'power':10}}
    settings = MMSettings(channels=channels, n_channels=2)

    event_thread = EventThread()
    event_thread.start()

    ni = NIDAQ(event_thread=event_thread, settings=settings)
    settings_view = SettingsView(event_thread)
    miniapp = MainGUI(event_thread=event_thread)
    miniapp.show()

    sys.exit(app.exec_())





if __name__ == "__main__":
    main()
