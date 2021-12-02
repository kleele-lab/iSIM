import nidaqmx
import nidaqmx.stream_writers
import numpy as np


class NIDAQ_Test():

    def __init__(self):

        self.system = nidaqmx.system.System.local()

        self.power488 = 2
        self.SamplingRate = 500
        self.SweepsPerFrame = 1
        self.ExpTime = 100
        self.NoFrames = int(2000/self.ExpTime)
        self.noPoints = self.SamplingRate*self.SweepsPerFrame

        self.DutyCycle=10/(self.SamplingRate*self.SweepsPerFrame)
        self.FrameRate=1/(self.ExpTime*self.SweepsPerFrame/1000)
        # DAQ specific parameters
        self.smplRate = int(np.round(round(self.SamplingRate*self.FrameRate*self.SweepsPerFrame)))

        self.task = nidaqmx.Task()
        self.task.ao_channels.add_ao_voltage_chan('Dev1/ao0') # galvo channel
        self.task.ao_channels.add_ao_voltage_chan('Dev1/ao2') # camera channel
        self.task.ao_channels.add_ao_voltage_chan('Dev1/ao3') # aotf blanking channel
        self.task.ao_channels.add_ao_voltage_chan('Dev1/ao4') # aotf 488 channel

        self.task.timing.cfg_samp_clk_timing(rate=self.smplRate, sample_mode=nidaqmx.constants.AcquisitionType.CONTINUOUS,
                                        samps_per_chan=self.SamplingRate*self.SweepsPerFrame)
        self.task.out_stream.regen_mode = nidaqmx.constants.RegenerationMode.DONT_ALLOW_REGENERATION
        self.stream = nidaqmx.stream_writers.AnalogMultiChannelWriter(self.task.out_stream, auto_start=False)
        self.stream.write_many_sample(np.zeros((self.task.number_of_channels, self.smplRate)))
        self.task.register_every_n_samples_transferred_from_buffer_event(2, self.makeData)

    def makeData(self, task_handle, every_n_samples_event_type, number_of_samples, callback_data):
        galvoData = self.makeGalvo()
        cameraData = self.makeCamera()
        laserData = self.makeAOTF()
        daqData = np.vstack((galvoData, cameraData, laserData))
        daqData = np.tile(daqData, self.NoFrames)
        self.stream.write_many_sample(daqData)
        return 0

    def startTask(self):
        self.task.start()

    def closeTask(self):
        self.task.close()

    def makeCamera(self):
        cameraData = self.makePulse(5,0,0)
        # cameraData = np.tile(cameraData, self.NoFrames)
        return cameraData

    def makeGalvo(self):
        # These parameters should be moved to init and have an option to be set
        Offset0=-0.15
        Amp0 = 0.75
        NoPoints = self.SamplingRate*self.SweepsPerFrame
        down1 = np.linspace(0,-Amp0,round(NoPoints/(4*self.SweepsPerFrame)))
        up = np.linspace(-Amp0,Amp0,round(NoPoints/(2*self.SweepsPerFrame)))
        down2 = np.linspace(Amp0,0,round(NoPoints/self.SweepsPerFrame)-round(NoPoints/(4*self.SweepsPerFrame))-round(NoPoints/(2*self.SweepsPerFrame)))
        galvoData = np.concatenate((down1, up, down2))
        galvoData = np.tile(galvoData, self.SweepsPerFrame)
        galvoData = galvoData + Offset0
        galvoData = galvoData[0:NoPoints]
        return galvoData

    def makeAOTF(self):
        aotfBlank = self.makeAOTFblank()
        aotf488 = self.makeAOTF488()
        laserData = np.vstack((aotfBlank, aotf488))
        return laserData

    def makeAOTFblank(self):
        Amp3=10
        aotfBlank = self.makePulse(0, Amp3, 0)
        return aotfBlank

    def makeAOTF488(self):
        aotf488 = self.makePulse(0, self.power488, 0)
        return aotf488

    def makePulse(self, start, end, offset):
        up = np.ones(int(self.DutyCycle*self.noPoints))*start
        down = np.ones(self.noPoints-int(self.DutyCycle*self.noPoints))*end
        pulse = np.concatenate((up,down)) + offset
        return pulse

daq = NIDAQ_Test()
daq.startTask()
input('Press Enter to exit')  # task runs for as long as ENTER is not pressed
daq.closeTask()
