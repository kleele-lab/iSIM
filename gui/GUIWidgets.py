import operator
import copy
import time
import sys
from typing import Tuple
from PyQt5 import QtGui, QtCore, QtWidgets
from pyqtgraph.functions import mkBrush, mkPen
from pyqtgraph.graphicsItems.GraphicsObject import GraphicsObject
import numpy as np
import time
from pyqtgraph import GraphicsLayoutWidget, ImageItem, PlotWidget, PlotCurveItem
from threading import Thread
from pymm_eventserver.event_thread import EventThread, MMSettings
from isimgui.MonogramCC import MonogramCC
from scipy.ndimage import center_of_mass
import qimage2ndarray


# Adjust for different screen sizes
QtWidgets.QApplication.setAttribute(QtCore.Qt.HighDpiScaleFactorRoundingPolicy.PassThrough)

class Colors(object):
    """ Defines colors for easy access in all widgets. """
    def __init__(self):
        self.blue = QtGui.QColor(25, 180, 210, alpha=150)
        self.red = QtGui.QColor(220, 20, 60, alpha=150)


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
        self.sliderMoved.connect(self.slider_moved)

        # Try to connect the Monogram Controller
        self.monogram = None
        self.my_event = False

    def slider_moved(self, e):
        self.my_event = True

    def connect_monogram(self, monogram):
        self.monogram = monogram
        self.monogram.monogram_stage_position_event.connect(self.monogram_event)

    def z_value_changed(self, pos):
        self.repaint()

        if self.my_event:
            print('Slider sending event')
            self.z_stage_position_python.emit(pos/100)
            self.my_event = False

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
        self.my_event = True
        self.setValue(pos)

    def keyPressEvent(self, event):
        if event.key() == 16777220:
            event.accept
            self.focusPos = self.handlePos()
            self.update()

    @QtCore.pyqtSlot(float)
    def monogram_event(self, relative_move: float):
        pos = self.value() + int(relative_move*150)
        self.my_event = True
        self.setValue(pos)

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

    def __init__(self, parent:QtWidgets.QWidget=None):
        super(PositionHistory, self).__init__(QtWidgets.QGraphicsScene(), parent=parent)
        # Set the properties for the window so that everything is shown and we don't have Scrollbars
        self.view_size = (3000, 3000)
        self.setBaseSize(self.view_size[0], self.view_size[1])
        # self.fitInView(0, 25,
        #     # -self.view_size[0], -self.view_size[1] + 25,
        #                self.view_size[0], self.view_size[1] - 50,
        #                QtCore.Qt.AspectRatioMode.KeepAspectRatio)
        self.setSceneRect(0, 25,
            # -self.view_size[0], -self.view_size[1] + 25,
                          self.view_size[0], self.view_size[1] - 50)
        self.scale(-1, -1)
        self.setVerticalScrollBarPolicy(QtCore.Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarPolicy.ScrollBarAlwaysOff)

        # Initialize the position of the stage and the parameters
        self.stage_pos = [0, 0]
        self.size_adjust = 10
        self.fov_size = (114/self.size_adjust, 114/self.size_adjust)
        self.sample_size = self.view_size
        pos = self.rectangle_pos(self.stage_pos)

        # Get the components of the GUI ready
        self.map = QtGui.QImage(self.sample_size[0], self.sample_size[1],
                                QtGui.QImage.Format.Format_RGB32)

        self.my_pixmap = self.scene().addPixmap(QtGui.QPixmap.fromImage(self.map))
        self.my_pixmap.setZValue(-100)
        self.fitInView()

        # Circle giving relation to coverslip
        diameter = self.view_size[0]/2
        self.circle = self.scene().addEllipse(QtCore.QRectF(0, 0, diameter, diameter),
                                              QtGui.QPen(Colors().red,3),
                                              QtGui.QBrush(QtGui.QColorConstants.Transparent))
        self.circle.setPos(self.sample_size[0]/2 - diameter/2, self.sample_size[1]/2 - diameter/2)
        self.circle.setZValue(-99)
        self.now_rect = self.scene().addRect(QtCore.QRectF(0, 0,
                                                           self.fov_size[0], self.fov_size[1]),
                                             QtGui.QPen(Colors().blue,1),
                                             QtGui.QBrush(QtGui.QColorConstants.Transparent))
        self.now_rect.setZValue(100)
        self.now_rect.setPos(pos[0], pos[1])
        self.arrow = self.scene().addPolygon(self.oof_arrow(),
                                QtGui.QPen(QtGui.QColorConstants.Transparent),
                                QtGui.QBrush(Colors().blue))
        self.arrow.setPos(100,100)
        self.arrow.setVisible(0)
        self.rect = QtCore.QRectF(pos[0], pos[1],
                                 self.fov_size[0], self.fov_size[1])

        self.laser = True
        self.stage_offset = [0, 0]

        # Enable Zoom
        self.setTransformationAnchor(QtWidgets.QGraphicsView.AnchorUnderMouse)
        self.setResizeAnchor(QtWidgets.QGraphicsView.AnchorUnderMouse)
        self._zoom = 0
        self.setDragMode(QtWidgets.QGraphicsView.DragMode.ScrollHandDrag)
        # self.setSceneRect(self.view_size[0]*0.45, self.view_size[1]*0.55,
        #                   self.view_size[0]/10, self.view_size[1]/10)
        # Start a Timer that checks if the laser is on and enhances at that position
        self.timer = QtCore.QTimer()
        self.timer.timeout.connect(self.increase_values)
        self.timer.start(1_000)


    def stage_moved(self, new_pos):
        self.stage_pos = new_pos
        new_pos = [x/10 for x in new_pos]
        pos = self.rectangle_pos(list(map(operator.sub, new_pos, self.stage_offset)))
        self.rect = QtCore.QRectF(pos[0], pos[1], self.fov_size[0], self.fov_size[1])
        # self.painter.drawRect(self.rect)
        self.my_pixmap.setPixmap(QtGui.QPixmap.fromImage(self.map))
        self.now_rect.setPos(QtCore.QPointF(pos[0], pos[1]))
        self.set_oof_arrow()
        self.repaint()
        self.xy_stage_position_python.emit(self.stage_pos)

    def rectangle_pos(self, pos):
        rect_pos = [int(self.sample_size[0]*0.5 + pos[0] - self.fov_size[0]/2),
                    int(self.sample_size[1]*0.5 + pos[1] - self.fov_size[1]/2)]
        return rect_pos

    def set_oof_arrow(self):
        pos = self.rectangle_pos(list(map(operator.sub, self.stage_pos, self.stage_offset)))
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
        elif pos[0] - self.sample_size[0]/2 > self.sample_size[0]/2:
            self.arrow.setPos(QtCore.QPointF(self.sample_size[0]-offset, y))
            self.arrow.setRotation(90)
        elif pos[0] - self.sample_size[0]/2  < -self.sample_size[0]/2:
            self.arrow.setRotation(-90)
            self.arrow.setPos(QtCore.QPointF(offset, y))
        elif pos[1] - self.sample_size[1]/2 < -self.sample_size[1]/2:
            self.arrow.setRotation(0)
            self.arrow.setPos(QtCore.QPointF(x, offset))
        elif pos[1] - self.sample_size[1]/2  > self.sample_size[1]/2:
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
        self.painter = self.define_painter()
        if self.laser:
            color = QtGui.QColor(255, 255, 255)
            color.setAlpha(self.laser)
            self.painter.brush().setColor(color)
            self.painter.drawRect(self.rect)
            self.my_pixmap.setPixmap(QtGui.QPixmap.fromImage(self.map))
        self.painter.end()

    def define_painter(self, alpha=10):
        painter = QtGui.QPainter(self.map)
        color = QtGui.QColor(255, 255, 255)
        color.setAlpha(alpha)
        brush = QtGui.QBrush(color)
        painter.setBrush(brush)
        painter.setPen(QtGui.QPen(QtGui.QColorConstants.Transparent))
        return painter

    def keyPressEvent(self, event):
        # print("KEY pressed: ", event.key())
        # print(event.modifiers() & QtCore.Qt.ShiftModifier)
        if event.modifiers() & QtCore.Qt.ShiftModifier:
            move_modifier = 0.2 * self.size_adjust
        else:
            move_modifier = 1 * self.size_adjust
        if event.key() == 16777236:
            event.accept()
            self.stage_pos[0] = self.stage_pos[0] - self.fov_size[0] * move_modifier
            self.stage_moved(self.stage_pos)
        if event.key() == 16777234:
            event.accept()
            self.stage_pos[0] = self.stage_pos[0] + self.fov_size[0] * move_modifier
            self.stage_moved(self.stage_pos)
        if event.key() == 16777235:
            event.accept()
            self.stage_pos[1] = self.stage_pos[1] + self.fov_size[1] * move_modifier
            self.stage_moved(self.stage_pos)
        if event.key() == 16777237:
            event.accept()
            self.stage_pos[1] = self.stage_pos[1] - self.fov_size[1] * move_modifier
            self.stage_moved(self.stage_pos)
        if event.key() == 16777220:
            "Enter: Reset drawn positions"
            self.map = QtGui.QImage(self.sample_size[0], self.sample_size[1],
                                    QtGui.QImage.Format.Format_Grayscale8)
            self.my_pixmap.setPixmap(QtGui.QPixmap.fromImage(self.map))
        if event.key() == 16777221:
            "NumPadEnter: reset position of rectangle"
            print(self.now_rect.pos())
            print(self.stage_offset)
            self.stage_offset = copy.deepcopy(self.stage_pos)
            self.stage_moved(self.stage_pos)
            print(self.stage_offset)
            print(self.stage_pos)
            print(self.now_rect.pos())

    def wheelEvent(self, event):
        if event.angleDelta().y() > 0:
            factor = 0.8
            self._zoom -= 1
        else:
            factor = 1.25
            self._zoom += 1
        if self._zoom > 0:
            self.scale(factor, factor)
        elif self._zoom == 0:
            self.fitInView()
        else:
            self._zoom = 0

    def fitInView(self, scale=False):
        rect = QtCore.QRectF(self.my_pixmap.pixmap().rect())
        # if not rect.isNull():
        self.setSceneRect(rect)
        unity = self.transform().mapRect(QtCore.QRectF(0, 0, 1, 1))
        self.scale(1 / unity.width(), 1 / unity.height())
        viewrect = self.viewport().rect()
        scenerect = self.transform().mapRect(rect)
        factor = min(viewrect.width() / scenerect.width(),
                        viewrect.height() / scenerect.height())
        self.scale(factor, factor)
        self._zoom = 0

    def resizeEvent(self, event):
        # self.setBaseSize(self.view_size[0], self.view_size[1])
        self.fitInView()
        self.scale(10, 10)
        self.centerOn(self.now_rect)
        # self.scale(10,10)
        # self.setSceneRect(0, 25, self.view_size[0], self.view_size[1] - 50)
        # self.fitInView(0, 25, self.view_size[0], self.view_size[1] - 50,
        #                QtCore.Qt.AspectRatioMode.KeepAspectRatio)
        # self.fitInView(0, 25,
        #             #    -self.view_size[0], -self.view_size[1] + 25,
        #                self.view_size[0], self.view_size[1] - 50,
        #                QtCore.Qt.AspectRatioMode.KeepAspectRatio)
        # self.setSceneRect(0, 25,
        #                 #   -self.view_size[0], -self.view_size[1] + 25,
        #                   self.view_size[0], self.view_size[1] - 50,)




class LiveView(QtWidgets.QGraphicsView):
    """ Mirror the last image received by Micro-Manager in a Python window """

    def __init__(self, parent=None):
        super(LiveView, self).__init__(QtWidgets.QGraphicsScene(), parent=parent)
        self.pixmap = QtGui.QPixmap(512, 512)
        self.setSceneRect(0, 0, 512, 512)
        self.image = self.scene().addPixmap(self.pixmap)

    def reset_scene_rect(self, shape: Tuple):
        self.setSceneRect(0, 0, *shape)

    def set_qimage(self, image: QtGui.QImage):
        self.image.setPixmap(QtGui.QPixmap.fromImage(image))
        self.update()


class AlignmentWidget(QtWidgets.QWidget):
    """ Takes the microscope image and displays the four extremes and the center. Adds points to
    peaks and gives other useful information for the alignment process"""

    def __init__(self, parent=None):
        width = height = 140
        self.window_offset = 62
        super().__init__()
        self.angle = -0.0665
        self.pixmap = QtGui.QPixmap(width,height)
        grid = QtWidgets.QGridLayout(self)
        top_bottom_offset = np.tan(abs(self.angle))*(1024-height/2) - self.window_offset
        self.view_top = AlignmentView(line_offset= - top_bottom_offset,
                                      expected_shape=(width,height),
                                      angle=self.angle)
        self.view_center = AlignmentView(center = True, expected_shape=(width,height),
                                         angle=self.angle)
        self.view_center.viewBox.disableAutoRange()
        self.view_center.viewBox.setRange(xRange = (35,105), yRange=(35,105))
        self.view_center.viewBox.setMouseMode(self.view_center.viewBox.RectMode)
        self.view_bottom = AlignmentView(line_offset=top_bottom_offset,
                                         expected_shape=(width,height), angle=self.angle)
        grid.addWidget(self.view_top, 0, 1, 1, 1)
        grid.addWidget(self.view_center, 0, 0, 2, 1)
        grid.addWidget(self.view_bottom, 1, 1, 1, 1)
        self.size = int(width/2)

    def add_image(self, image):
        qimage = image.raw_image
        self.view_top.set_qimage(qimage[0:self.size*2,
                                        1024-self.size-self.window_offset:1024+self.size-self.window_offset])
        self.view_center.set_qimage(qimage[1024-self.size:1024+self.size,
                                           1024-self.size:1024+self.size])
        self.view_bottom.set_qimage(qimage[2048-self.size*2:2048,
                                           1024-self.size+self.window_offset-1:1024+self.size+self.window_offset-1])


class AlignmentView(GraphicsLayoutWidget):
    """ Extend live view with functionality for alignment """

    def __init__(self, parent=None, center:bool = False,
                 line_offset:float = 0., expected_shape:Tuple = (160, 160),
                 angle: float = 0.65):
        super().__init__()
        self.setSceneRect(0, 0, expected_shape[0], expected_shape[1])
        self.viewBox = self.addViewBox()
        self.viewBox.setAspectLocked()
        self.viewBox.invertY()
        self.pg_image = ImageItem()
        self.pg_image.setOpts(axisOrder='row-major')
        self.viewBox.addItem(self.pg_image)
        self.raw_data = np.ones(expected_shape)
        self.pointer_radius = 5
        self.pointers = []
        self.old_pointers = []
        self.peaks = []
        self.peak_pos = []
        self.window_size = 20
        self.fit_number = 0


        self.line = LineItem(center=center, offset=line_offset, shape=expected_shape, angle=angle)
        self.viewBox.addItem(self.line)

        self.peak_timer = QtCore.QTimer()
        self.peak_timer.timeout.connect(self.update_peaks)
        self.peak_timer.start(5000)
        self.fit_timer = QtCore.QTimer()
        self.fit_timer.timeout.connect(self.update_peak_location)
        self.fit_timer.start(500)
        self.reset_line()

    def update_peaks(self):
        self.get_peaks()

    def update_peak_location(self):
        self.fit_peaks()
        self.set_pointers()

    def set_qimage(self, image_data):
        self.raw_data = image_data
        self.pg_image.setImage(image_data)
        self.update()

    def get_peaks(self):
        perf0 = time.perf_counter()
        self.fit_timer.stop()
        data = np.copy(self.raw_data)
        mean_image = np.mean(data)
        data[:self.window_size,:] = mean_image * np.ones_like(data[:self.window_size,:])
        data[:,:self.window_size] = mean_image * np.ones_like(data[:,:self.window_size])
        data[-self.window_size:,:] = mean_image * np.ones_like(data[-self.window_size:,:])
        data[:,-self.window_size:] = mean_image * np.ones_like(data[:,-self.window_size:])
        max_value = 1000000

        perf1 = time.perf_counter()
        print("Part 1:", perf1 - perf0)

        self.old_pointers = self.pointers
        self.pointers = []
        self.peaks = []
        while max_value > mean_image*1.5:
            max_value = np.max(data)
            max_pixel = np.where(data == max_value)
            max_pixel = [int(pixel[0]) for pixel in max_pixel]
            if np.min(max_pixel) > self.window_size and max_pixel[0] < data.shape[0]-self.window_size and max_pixel[1] < data.shape[1]-self.window_size:
                data[max_pixel[0]-self.window_size:max_pixel[0]+self.window_size+1,
                     max_pixel[1]-self.window_size:max_pixel[1]+self.window_size+1] = np.zeros((self.window_size*2+1,
                                                                                                self.window_size*2+1))
                self.peaks.append(max_pixel)
                self.add_pointer()
                if len(self.peaks) > 16:
                    break
            else:
                data[max_pixel[0], max_pixel[1]] = np.mean(data)
        self.fit_number = 0
        self.fit_timer.start()
        perf2 = time.perf_counter()
        print("Part 2:", perf2 - perf1)

    def fit_peaks(self):
        data = np.copy(self.raw_data)
        self.peak_pos = []

        for index, peak in enumerate(self.peaks):
            peak_data = data[peak[0]-self.window_size:peak[0]+self.window_size+1,
                             peak[1]-self.window_size:peak[1]+self.window_size+1]
            mask = peak_data < np.mean(peak_data)*1.5
            peak_data[mask] = 0
            x, y = center_of_mass(peak_data)
            x_image = peak[0] + x - (self.window_size - 0.5)
            y_image = peak[1] + y - (self.window_size - 0.5)
            self.peak_pos.append([x_image, y_image])
        self.fit_number += 1


    def set_pointers(self):
        if self.fit_number == 1:
            for pointer in self.old_pointers:
                self.viewBox.removeItem(pointer)
        for index, peak in enumerate(self.peak_pos):
            pointer = self.pointers[index]
            pointer.setPosition(peak)
        if self.fit_number == 1:
            for pointer in self.pointers:
                pointer.show()

    def add_pointer(self):
        pointer = CrossItem()
        pointer.hide()
        self.viewBox.addItem(pointer)
        self.pointers.append(pointer)

    def reset_line(self):
        self.line.setPosition([0, self.raw_data.shape[1]/2])

    # def centroidnp(self, data):
    #     h, w = data.shape
    #     x = np.arange(w)
    #     y = np.arange(h)
    #     vx = data.sum(axis=0)
    #     vx = vx/vx.sum()
    #     vy = data.sum(axis=1)
    #     vy = vy/vy.sum()
    #     return np.dot(vx,x),np.dot(vy,y)


class LineItem(GraphicsObject):
    """Alignment Line with angle and offset

    Original angle: -0.063948864"""
    def __init__(self, offset:float = -30, angle:float = -0.065, center:bool = False,
                 shape:Tuple = (160,160)):
        super().__init__()
        self.offset = offset
        self.angle = angle
        self.shape = shape
        self.center = center
        self.picture = QtGui.QPicture()
        self.color = '#00FFFF'
        self.generatePicture()
        self.setZValue(90)


    def generatePicture(self):
        """ Generate the line. The size should at some point be set depending on the Range of
        the ViewBox for example to ensure always the same apparent size. """
        size = self.shape
        painter = QtGui.QPainter(self.picture)
        painter.setPen(mkPen(color=self.color, width=2))
        dx = np.tan(self.angle)*size[1]/2
        painter.drawLine(-dx, size[1], +dx, 0)
        if self.center:
            painter.drawLine(-size[0]/2, size[1]/2-dx, size[0]/2, size[1]/2+dx)
        painter.end()

    def setPosition(self, pos):
        """ set the Position of the line after translating to a QPointF"""
        pos = QtCore.QPointF(pos[1]+0.5 + self.offset, pos[0] + 0.5)
        self.setPos(pos)

    def paint(self, *painter):
        """ I think this is used by the ViewBox when displaying the line """
        painter[0].drawPicture(0, 0, self.picture)

    def boundingRect(self):
        """ Bounding rectangule of the line as QRectF """
        return QtCore.QRectF(self.picture.boundingRect())


class CrossItem(GraphicsObject):
    """ A cross that can be added to a pg.ViewBox to point """
    def __init__(self, rect=QtCore.QRectF(0, 0, 1, 1), color='#CC0000', parent=None):

        super().__init__(parent)
        self._rect = rect
        self.color = color
        self.picture = QtGui.QPicture()
        self.generatePicture()
        self.setZValue(100)

    @property
    def rect(self):
        """ original rectangle give at initialization """
        return self._rect

    def generatePicture(self, pos=(0, 0)):
        """ Generate the cross. The size should at some point be set depending on the Range of
        the ViewBox for example to ensure always the same apparent size. """
        size = 5
        painter = QtGui.QPainter(self.picture)
        painter.setPen(mkPen(color=self.color, width=3))
        painter.setBrush(mkBrush(color=self.color))
        painter.drawLine(pos[0]-size, pos[1]-size, pos[0]+size, pos[1]+size)
        painter.drawLine(pos[0]+size, pos[1]-size, pos[0]-size, pos[1]+size)
        painter.end()

    def setPosition(self, pos):
        """ set the Position of the cross after translating to a QPointF"""
        pos = QtCore.QPointF(pos[1], pos[0])
        self.setPos(pos)

    def paint(self, *painter):
        """ I think this is used by the ViewBox when displaying the cross """
        painter[0].drawPicture(0, 0, self.picture)

    def boundingRect(self):
        """ Bounding rectangule of the cross as QRectF """
        return QtCore.QRectF(self.picture.boundingRect())


class RunningMean(PlotWidget):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.mean = PlotCurveItem([], pen=QtGui.QPen(QtGui.QColor('#505050')))
        self.addItem(self.mean)
        self.means = []
        self.window_size = int(300/2)

    def add_image(self, image):
        image = image.raw_image[1024-self.window_size:1024 + self.window_size,
                                1024-self.window_size:1024 + self.window_size].flatten()
        sorted_image = np.sort(image)
        self.add_value(np.mean(sorted_image[-20:]))


    def add_value(self, new_value):
        if len(self.means) >= 200:
            self.means.pop(0)
        if len(self.means) > 5:
            self.means.append(np.mean(self.means[-5:] + [new_value]))
        else:
            self.means.append(new_value)
        self.mean.setData(self.means)


class SettingsView(QtWidgets.QWidget):
    def __init__(self, event_thread):
        super().__init__()
        # event_thread.mda_settings_event.connect(self.update_settings)

    # @QtCore.pyqtSlot(object)
    # def update_settings(self, new_settings):
    #     self.settings = new_settings
    #     print(self.settings)



class MiniApp(QtWidgets.QWidget):
    """ Makes a mini App that shows off the capabilities of the Widgets implemented here """
    def __init__(self, parent=None):
        super(MiniApp, self).__init__(parent=parent)
        self.setLayout(QtWidgets.QHBoxLayout())
        self.position_history = PositionHistory()
        self.layout().addWidget(self.position_history)
        # self.focus_slider = FocusSlider()
        # self.layout().addWidget(self.focus_slider)
        # # self.layout().addWidget(LiveView())
        # self.al_widget = AlignmentWidget()
        # self.layout().addWidget(self.al_widget)
        self.setStyleSheet("background-color:black;")
        try:
            self.monogram = MonogramCC()
            self.focus_slider.connect_monogram(self.monogram)
        except OSError as e:
            print(e)


class TestThread(Thread):
    """ Draws into the pyqtgraph window to show a potential value being added there """
    def __init__(self, app):
        super(TestThread, self).__init__(target=self.do_work, daemon=True)
        self.app = app

    def do_work(self):
        for t in range(30):
            self.app.al_widget.mean_running.add_value(t % 10)
            time.sleep(0.2)


if __name__ == '__main__':
    import time
    app = QtWidgets.QApplication(sys.argv)
    miniapp = MiniApp()
    miniapp.show()
    # thread = TestThread(miniapp)
    # thread.start()

    # settings_view = SettingsView()
    # settings_view.show()

    sys.exit(app.exec_())
