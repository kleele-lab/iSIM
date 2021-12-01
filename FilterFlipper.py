import clr
import time
import ctypes

clr.AddReference('C:/Program Files/Thorlabs/Kinesis/Thorlabs.MotionControl.DeviceManagerCLI.dll')
clr.AddReference('C:/Program Files/Thorlabs/Kinesis/Thorlabs.MotionControl.GenericMotorCLI.dll')
clr.AddReference('C:/Program Files/Thorlabs/Kinesis/Thorlabs.MotionControl.FilterFlipperCLI.dll')

import Thorlabs.MotionControl.DeviceManagerCLI as DeviceManagerCLI
import Thorlabs.MotionControl.GenericMotorCLI as GenericMotorCLI
import Thorlabs.MotionControl.FilterFlipperCLI as FilterFlipperCLI
from System import UInt32, Int32


class FilterFlipper(object):

    def __init__(self):
        DeviceManagerCLI.DeviceManagerCLI.BuildDeviceList()
        self.availableDevices = DeviceManagerCLI.DeviceManagerCLI.GetDeviceList()
        self.device = None
        self.serialNo = None
        self._timeout = 21000    # Default timeout time for settings change
        self._timeoutMove = 10000
        self._tpolling = 250
        self._info = None

    def connect(self, flipperNo):
        self.serialNo = self.availableDevices[flipperNo]
        self.device = FilterFlipperCLI.FilterFlipper.CreateFilterFlipper(self.serialNo)
        self.device.ClearDeviceExceptions()
        self.device.Connect(self.serialNo)
        if not self.device.IsSettingsInitialized():
            self.device.WaitForSettingsInitialized(self._timeout)
        self.device.StartPolling(self._tpolling)
        self.device.EnableDevice()
        self._info = self.device.GetDeviceInfo()
        self.setUpDown()

    def setPos(self, position):
        self.device.SetPosition(UInt32(position), Int32(self._timeoutMove))
        self.device.Wait(self._timeoutMove)

    def moveUp(self):
        self.setPos(self._upPos)

    def moveDown(self):
        self.setPos(self._downPos)

    def home(self):
        workDone = self.device.InitializeWaitHandler()
        self.device.Home(workDone)
        self.device.Wait(self._timeoutMove)

    def disconnect(self):
        self.device.StopPolling()
        self.device.Disconnect()

    def setUpDown(self):
        if self.serialNo == '37871830':
            self._upPos = 2
            self._downPos = 1
        elif self.serialNo == '37872141':
            self._upPos = 1
            self._downPos = 2
        else:
            self._upPos = 1
            self._downPos = 2
            print('I dont know the Up/Down Position for this Flipper')


def testFlippers():
    flipper = FilterFlipper()
    availableDevices = flipper.availableDevices
    print(availableDevices)
    for i in range(len(availableDevices)):
        print(i)
        flipper.connect(i)

        flipper.moveUp()
        flipper.moveDown()
        flipper.disconnect()


if __name__ == '__main__':
    testFlippers()
