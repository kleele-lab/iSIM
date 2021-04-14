import clr


clr.AddReference('C:/Program Files/Thorlabs/Kinesis/Thorlabs.MotionControl.DeviceManagerCLI.dll')

import Thorlabs.MotionControl.DeviceManagerCLI as DeviceManager


devList = DeviceManager.DeviceManagerCLI.GetDeviceList()
print(devList)
