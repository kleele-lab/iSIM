
import pygame
import threading
from PyQt5.QtCore import  pyqtSlot, pyqtSignal, QObject, QCoreApplication, QTimer
import time
import sys

CUTOFF_SPEEDUP = 80 # This is 1/ms for last value change
# CUTOFF_SPEEDDOWN = 5
CUTOFF_SPEED = 200


class MonogramCC(QObject):

    monogram_stage_position_event = pyqtSignal(float)

    def __init__(self):
        super().__init__()
        pygame.init()
        self.initController()
        self.ZPosition = self.device.get_axis(0)
        self.oldValue = self.device.get_axis(0)
        self.offset = self.oldValue
        self.last_time = time.perf_counter()
        self.turn = 0
        self.thread = threading.Thread(target=self.startListen, args=())
        self.thread.daemon = True                            # Daemonize thread
        self.thread.start()

    def startListen(self):
        done = False
        print('started')
        while done == False:
            event = pygame.event.wait()
            if event.type == 1536:  # AxisMotion
                self.updatePos(event.value)
            if event.type == 1540:  # ButtonUp
                if event.button == 0:
                    pygame.quit()
                    done = True
                if event.button == 1:
                    self.resetPos()

    def resetPos(self):
        self.ZPosition = 0
        self.offset = self.device.get_axis(0)
        self.turn = 0
        print('reset')

    def updatePos(self, newValue):
        if self.oldValue > 0.5 and newValue < -0.5:
            self.turn = self.turn + 2
        elif self.oldValue < -0.5 and newValue > 0.5:
            self.turn = self.turn - 2
        self.ZPosition = newValue + self.turn - self.offset
        relative_move = self.get_relative_move(newValue)
        relative_move_scaled = self.scale_relative_move(relative_move)

        self.oldValue = newValue

        self.monogram_stage_position_event.emit(relative_move_scaled)
        # print(relative_move_scaled)
        # print(self.ZPosition)

    def initController(self):
        joystick_count = pygame.joystick.get_count()
        if joystick_count == 0:
            # No joysticks!
            raise OSError('No joystick found')
        else:
            # Use joystick #0 and initialize it
            self.device = pygame.joystick.Joystick(0)
            self.device.init()

    def get_relative_move(self, newValue: float) -> float:
        relative_move = newValue - self.oldValue
        if relative_move < -1 or (0.0001 > relative_move > 0):
            relative_move = 0.0079
        elif relative_move > 1 or (-0.0001 < relative_move < 0):
            relative_move = -0.0079
        return relative_move

    def scale_relative_move(self, relative_move: float) -> float:
        now = time.perf_counter()
        speed = 1/(now - self.last_time)
        speed = min([speed, CUTOFF_SPEED])
        self.last_time = now
        if speed > CUTOFF_SPEEDUP:
            relative_move = (speed - CUTOFF_SPEEDUP +5)/5 * relative_move
        # elif speed < CUTOFF_SPEEDDOWN:
        #     relative_move = speed/CUTOFF_SPEEDDOWN * relative_move
        print(self.ZPosition)
        return relative_move

def main(control:bool = False):
    app = QCoreApplication(sys.argv)
    try:
        obj = MonogramCC()
    except IOError as e:
        print(e)
        sys.exit()

    if control:
        import MicroManagerControl
        micro_control = MicroManagerControl.MicroManagerControl()
        obj.monogram_stage_position_event.connect(micro_control.track_z_change)
    # Make this interruptable by Ctrl+C
    timer = QTimer()
    timer.timeout.connect(lambda: None)
    timer.start(500)

    sys.exit(app.exec_())


if __name__ == '__main__':
    main()