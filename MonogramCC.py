
import pygame
from PyQt5.QtCore import  pyqtSlot, pyqtSignal, QObject, QCoreApplication, QTimer, QThread
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
        # self.bridge = Bridge()
        # self.core = self.bridge.get_core()

        self.thread = QThread()
        self.worker = self.Listener(self.device, self)
        self.worker.moveToThread(self.thread)
        self.worker.monogram_stage_position_event.connect(self.monogram_stage_position_event)
        self.worker.started_moving.connect(self.start_moving)
        self.thread.started.connect(self.worker.startListen)
        self.thread.start()

        # self.stop_moving_timer = QTimer()
        # self.z_update_timer.timeout.connect(self.stop_moving)
        # self.z_update_timer.start(1000)
        self.moving = False

    def stop_moving(self):
        self.moving = False

    def start_moving(self):
        self.moving = True

    def initController(self):
        joystick_count = pygame.joystick.get_count()
        if joystick_count == 0:
            # No joysticks!
            raise OSError('No joystick found')
        else:
            # Use joystick #0 and initialize it
            self.device = pygame.joystick.Joystick(0)
            self.device.init()


    class Listener(QObject):
        monogram_stage_position_event = pyqtSignal(float)
        started_moving = pyqtSignal(float)
        def __init__(self, device, parent):
            super().__init__()
            self.device = device
            self.parent = parent
            self.ZPosition = self.device.get_axis(0)
            self.oldValue = self.device.get_axis(0)
            self.offset = self.oldValue
            self.last_time = time.perf_counter()
            self.turn = 0
            self.total_relative_move = 0
            self.last_send = time.perf_counter()

        def startListen(self):
            done = False
            print('Monogram started')
            while done == False:
                event = pygame.event.wait()
                if event.type == 1536:  # AxisMotion
                    if not self.parent.moving:
                        self.parent.moving = True
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
            self.total_relative_move = self.total_relative_move + relative_move_scaled
            self.send_move()

        def send_move(self):
            now = time.perf_counter()
            if now - self.last_send > 0.05:
                self.monogram_stage_position_event.emit(self.total_relative_move)
                # try:
                #     self.core.set_relative_position(self.total_relative_move)
                # except:
                #     print("Out of range!?")
                self.total_relative_move = 0
                self.last_send = now


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