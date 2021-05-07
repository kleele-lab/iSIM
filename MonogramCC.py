
import pygame
import threading

pygame.init()



class MonogramCC():

    def __init__(self):
        self.initController()
        status = self.check_controller()
        if not status:
            raise IOError
        self.ZPosition = self.device.get_axis(0)
        self.oldValue  = self.device.get_axis(0)
        self.offset = self.oldValue
        self.turn = 0
        self.thread = threading.Thread(target=self.startListen, args=())
        self.thread.daemon = True                            # Daemonize thread
        self.thread.start()

    def startListen(self):
        done=False

        while done==False:
            event = pygame.event.wait()
            if event.type == 1536: # AxisMotion
                self.updatePos(event.value)
            if event.type == 1540: # ButtonUp
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
        self.oldValue = newValue
        print(self.ZPosition)

    def initController(self):
        joystick_count=pygame.joystick.get_count()
        if joystick_count == 0:
            # No joysticks!
            print ("Error, I didn't find any joysticks.")
        else:
            # Use joystick #0 and initialize it
            self.device = pygame.joystick.Joystick(0)
            self.device.init()

    def check_controller(self):
        try:
            print(self.device)
            return True
        except AttributeError:
            print('No controller connected')
            return False


if __name__ == '__main__':
    MonogramCC()
    input('Wait until closed by Keyboard')
