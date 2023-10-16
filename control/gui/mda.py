from pymmcore_widgets.mda._core_mda import MDAWidget
from qtpy.QtWidgets import QApplication
from pymmcore_plus import CMMCorePlus

mmc = CMMCorePlus()
mmc.loadSystemConfiguration()



app = QApplication([])
frame = MDAWidget(mmcore=mmc)
frame.setWindowTitle("MyMDA")
frame.show()
app.exec_()
