from gui.GUIWidgets import SettingsView
import sys
from PyQt5 import QtWidgets
from event_thread import EventThread

app = QtWidgets.QApplication(sys.argv)

event_thread = EventThread()
event_thread.start()
settings_view = SettingsView(event_thread)
settings_view.show()

sys.exit(app.exec_())
