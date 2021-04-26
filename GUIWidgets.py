import sys
from PyQt5 import QtGui, QtCore, QtWidgets, QtTest


class Colors(object):
    """ Defines colors for easy access in all widgets. """
    def __init__(self):
        self.blue = QtGui.QColor(25, 180, 210, alpha = 150)


class FocusSlider(QtWidgets.QSlider):

    z_stage_position_python = QtCore.pyqtSignal(float)

    def __init__(self, parent=None):
        super(FocusSlider, self).__init__(QtCore.Qt.Vertical, parent=parent)
        self.focusPos = 50
        self.step = 100
        self.setStyleSheet(self.stylesheet())
        self.arrows = self.getArrows()
        self.setMaximum(20200)
        self.valueChanged.connect(self.z_value_changed)

    def z_value_changed(self, pos):
        self.repaint()
        self.z_stage_position_python.emit(pos/100)

    def paintEvent(self, e):
        super().paintEvent(e)
        qp = QtGui.QPainter(self)
        qp.drawPixmap(75,self.focusPos,self.arrows[0])
        qp.drawPixmap(5,self.focusPos,self.arrows[1])
        qp.setPen(QtCore.Qt.gray)
        font = qp.font()
        font.setPixelSize(16)
        qp.setFont(font)
        qp.drawText(93 , self.handlePos()+18 , str(self.zPos()))

    def wheelEvent(self,event):
        pos = self.value()+int((event.angleDelta().y()/120)*self.step)
        self.setValue(pos)

    def keyPressEvent(self, event):
        if event.key() == 16777220:
            event.accept
            self.focusPos = self.handlePos()
            self.update()

    def handlePos(self):
        style = self.style()
        opt = QtWidgets.QStyleOptionSlider()
        self.initStyleOption(opt)
        rectHandle = style.subControlRect(QtWidgets.QStyle.CC_Slider, opt,
                                          QtWidgets.QStyle.SC_SliderHandle, self)
        handlePos = rectHandle.top()-1
        return handlePos

    def zPos(self):
        return self.value()/100

    def stylesheet(_):
        with open('assets/FocusSlider_style.txt') as f:
            style = f.read()
        return style

    def getArrows(_):
        arrows = [QtGui.QPixmap("assets/focus_slider_arrow.png")]
        arrows[0] = arrows[0].scaledToWidth(20)
        transform = QtGui.QTransform().rotate(180)
        arrows.append(arrows[0].transformed(transform, QtCore.Qt.SmoothTransformation))
        return arrows


class PositionHistory(QtWidgets.QGraphicsView):
    """ This is a widget that records the history of where the stage of the microscope has
    been for the given sample. It visualizes the time spent at a specific position on a grid
    with rectangles that get brighter for the more time spent at a position. This is also
    dependent on if the laser light was on at the given time."""
    xy_stage_position_python = QtCore.pyqtSignal(object)

    def __init__(self, parent=None):
        super(PositionHistory, self).__init__(QtWidgets.QGraphicsScene(), parent=parent)
        # Set the properties for the window so that everything is shown and we don't have Scrollbars
        self.view_size = (1500, 1500)
        self.setBaseSize(self.view_size[0], self.view_size[1])
        self.fitInView(0, 25, self.view_size[0], self.view_size[1] - 50,
                       QtCore.Qt.AspectRatioMode.KeepAspectRatio)
        self.setSceneRect(0, 25, self.view_size[0], self.view_size[1] - 50)
        self.setVerticalScrollBarPolicy(QtCore.Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarPolicy.ScrollBarAlwaysOff)


        # Initialize the position of the stage and the parameters
        self.stage_pos = [0, 0]
        self.fov_size = (81, 81)
        self.sample_size = self.view_size
        pos = self.rectangle_pos(self.stage_pos)

        # Get the components of the GUI ready
        self.map = QtGui.QImage(self.sample_size[0], self.sample_size[1],
                                QtGui.QImage.Format.Format_RGB32)
        self.painter = self.define_painter()
        self.pixmap = self.scene().addPixmap(QtGui.QPixmap.fromImage(self.map))
        self.now_rect = self.scene().addRect(QtCore.QRectF(0, 0,
                                                           self.fov_size[0], self.fov_size[1]),
                                             QtGui.QPen(Colors().blue,4),
                                             QtGui.QBrush(QtGui.QColorConstants.Transparent))
        self.now_rect.setPos(pos[0], pos[1])
        self.arrow = self.scene().addPolygon(self.oof_arrow(),
                                QtGui.QPen(QtGui.QColorConstants.Transparent),
                                QtGui.QBrush(Colors().blue))
        self.arrow.setPos(100,100)
        self.arrow.setVisible(0)
        self.rect = QtCore.QRectF(pos[0], pos[1],
                                 self.fov_size[0], self.fov_size[1])


        self.laser = True

        # Start a Timer that checks if the laser is on and enhances at that position
        self.timer = QtCore.QTimer()
        self.timer.timeout.connect(self.increase_values)
        self.timer.start(1_000)

    def stage_moved(self, new_pos):
        self.stage_pos = new_pos
        pos = self.rectangle_pos(new_pos)
        self.rect = QtCore.QRectF(pos[0], pos[1], self.fov_size[0], self.fov_size[1])
        # self.painter.drawRect(self.rect)
        self.pixmap.setPixmap(QtGui.QPixmap.fromImage(self.map))
        self.now_rect.setPos(QtCore.QPointF(pos[0], pos[1]))
        self.set_oof_arrow()
        self.repaint()
        self.xy_stage_position_python.emit(new_pos)

    def rectangle_pos(self, pos):
        rect_pos = [int(self.sample_size[0]*0.5 + pos[0] - self.fov_size[0]/2),
                    int(self.sample_size[1]*0.5 + pos[1] - self.fov_size[1]/2)]
        return rect_pos

    def set_oof_arrow(self):
        pos = self.rectangle_pos(self.stage_pos)
        y = self.check_limits(pos[1]+self.fov_size[1]/2)
        x = self.check_limits(pos[0]+self.fov_size[0]/2)
        self.arrow.setVisible(1)
        offset = 25
        if x == offset and y == offset:
            self.arrow.setPos(QtCore.QPointF(offset, offset))
            self.arrow.setRotation(-45)
        elif x == offset and y == self.sample_size[0]-offset:
            self.arrow.setPos(QtCore.QPointF(offset, self.sample_size[1]-offset))
            self.arrow.setRotation(-135)
        elif x == self.sample_size[0]-offset and y == self.sample_size[0]-offset:
            self.arrow.setPos(QtCore.QPointF(self.sample_size[0]-offset, self.sample_size[1]-offset))
            self.arrow.setRotation(135)
        elif x == self.sample_size[0]-offset and y == offset:
            self.arrow.setPos(QtCore.QPointF(self.sample_size[0]-offset, offset))
            self.arrow.setRotation(45)
        elif self.stage_pos[0] > self.sample_size[0]/2:
            self.arrow.setPos(QtCore.QPointF(self.sample_size[0]-offset, y))
            self.arrow.setRotation(90)
        elif self.stage_pos[0] < -self.sample_size[0]/2:
            self.arrow.setRotation(-90)
            self.arrow.setPos(QtCore.QPointF(offset, y))
        elif self.stage_pos[1] < -self.sample_size[1]/2:
            self.arrow.setRotation(0)
            self.arrow.setPos(QtCore.QPointF(x, offset))
        elif self.stage_pos[1] > self.sample_size[1]/2:
            self.arrow.setRotation(180)
            self.arrow.setPos(QtCore.QPointF(x, self.sample_size[1]-offset))
        else:
            self.arrow.setVisible(0)

    def check_limits(self, pos):
        if pos < 0:
            pos = 25
        elif pos > self.sample_size[0]:
            pos = self.sample_size[0]-25
        return pos

    def oof_arrow(self):
        arrow = QtGui.QPolygonF()
        arrow.append(QtCore.QPointF(-20, 0))
        arrow.append(QtCore.QPointF(0,-20))
        arrow.append(QtCore.QPointF(20, 0))
        arrow.append(QtCore.QPointF(-20, 0))
        return arrow

    def increase_values(self):
        if self.laser:
            self.painter.drawRect(self.rect)
            self.pixmap.setPixmap(QtGui.QPixmap.fromImage(self.map))

    def define_painter(self):
        painter = QtGui.QPainter(self.map)
        color = QtGui.QColor(255, 255, 255)
        color.setAlpha(10)
        brush = QtGui.QBrush(color)
        painter.setBrush(brush)
        painter.setPen(QtGui.QPen(QtGui.QColorConstants.Transparent))
        return painter

    def keyPressEvent(self, event):
        if event.key() == 16777236:
            event.accept
            self.stage_pos[0] = self.stage_pos[0] + self.fov_size[0]
            self.stage_moved(self.stage_pos)
        if event.key() == 16777234:
            event.accept
            self.stage_pos[0] = self.stage_pos[0] - self.fov_size[0]
            self.stage_moved(self.stage_pos)
        if event.key() == 16777235:
            event.accept
            self.stage_pos[1] = self.stage_pos[1] - self.fov_size[1]
            self.stage_moved(self.stage_pos)
        if event.key() == 16777237:
            event.accept
            self.stage_pos[1] = self.stage_pos[1] + self.fov_size[1]
            self.stage_moved(self.stage_pos)
        if event.key() == 16777220:
            self.painter.end()
            self.map = QtGui.QImage(self.sample_size[0], self.sample_size[1],
                                    QtGui.QImage.Format.Format_Grayscale8)
            self.pixmap.setPixmap(QtGui.QPixmap.fromImage(self.map))
            self.painter = self.define_painter()

    def resizeEvent(self, event):
        self.setSceneRect(0, 25, self.view_size[0], self.view_size[1] - 50)
        self.setBaseSize(self.view_size[0], self.view_size[1])
        self.fitInView(0, 25, self.view_size[0], self.view_size[1] - 50,
                       QtCore.Qt.AspectRatioMode.KeepAspectRatio)


class MiniApp(QtWidgets.QWidget):
    """ Makes a mini App that shows off the capabilities of the Widgets implemented here """
    def __init__(self, parent = None):
        super(MiniApp, self).__init__(parent=parent)
        self.setLayout(QtWidgets.QHBoxLayout())
        self.layout().addWidget(PositionHistory())
        self.layout().addWidget(FocusSlider())
        self.setStyleSheet("background-color:black;")


if __name__ == '__main__':
    import time
    app = QtWidgets.QApplication(sys.argv)
    miniapp = MiniApp()
    miniapp.show()
    sys.exit(app.exec_())
