""" This was an attempt to use pymmcore_plus to get the events.
But this connects directly to an pymmcore that has nothing to do with
the core that micromanager itself is using if we run it. So no way to
use the micromanager GUI with this. Napari-micromanager is based on
this though. So if you would like to go there at some point, this might
be helpful. Willi Stepp 21-10-29"""


from pymmcore_plus import RemoteMMCore
from PyQt5.QtCore import QObject
from PyQt5 import QtWidgets
from PyQt5.QtWidgets import QApplication
from PyQt5.QtCore import QObject, pyqtSignal
import time
import threading
import os

class EventThread(QtWidgets.QWidget):

    acquisition_started_event = pyqtSignal()

    def __init__(self):
        super().__init__()

        self._mmc = RemoteMMCore()
        self.sig = self._mmc.events
        self.sig.sequenceStarted.connect(self.seq_started)
        self.thread_stop = threading.Event()
        print('EventThread initialized')
        print('Starting Acqu')
        print(self._mmc.getLastImage())


    def seq_started(self, input):
        print('seq started')

    def start(self, daemon=True):
        self.thread = threading.Thread(daemon=daemon)
        self.thread.start()

    def stop(self):
        self.thread_stop.set()
        self.thread.join()


def main():
    app = QApplication([])
    window = EventThread()
    window.show()
    app.exec_()


if __name__ == "__main__":
    main()
