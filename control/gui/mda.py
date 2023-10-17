from pymmcore_widgets.mda._core_mda import MDAWidget
from qtpy.QtWidgets import QApplication, QPushButton
from pymmcore_plus import CMMCorePlus

mmc = CMMCorePlus()
mmc.loadSystemConfiguration()

import useq
def print_seq(self, seq: useq.MDASequence):
    print(seq.yaml())




if __name__ == "__main__":

    app = QApplication([])
    frame = MDAWidget(mmcore=mmc)
    frame.setWindowTitle("MyMDA")
    frame.show()

    button = QPushButton("Test")
    button.pressed.connect(lambda: print_seq(None, frame.value()))
    button.show()

    app.exec_()
