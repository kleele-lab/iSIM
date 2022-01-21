from data_structures import MMSettings
from gui.GUIWidgets import SettingsView
import sys
from PyQt5 import QtWidgets
from event_threadQ import EventThread
from gui.MainGUI import MainGUI
from hardware.nidaq import NIDAQ


def main():
    app = QtWidgets.QApplication(sys.argv)

    channels = {'488': {'name':'488', 'use': True, 'exposure': 100, },
                '561': {'name':'561', 'use': True, 'exposure': 100, }}
    settings = MMSettings(channels=channels, n_channels=2)
    settings.slices = [109, 110, 111]

    event_thread = EventThread()
    event_listener = event_thread.listener
    # event_thread.start()

    ni = NIDAQ(event_thread=event_listener, settings=settings)
    settings_view = SettingsView(event_listener)
    miniapp = MainGUI(event_thread=event_listener)
    miniapp.show()

    ni.set_start_z_position.connect(miniapp.mm_interface.set_z_position)

    sys.exit(app.exec_())



if __name__ == "__main__":
    main()
