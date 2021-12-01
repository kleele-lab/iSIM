from pycromanager import Bridge, core, Acquisition
import pycromanager
import threading
import re
import zmq
import json
from PyQt5.QtCore import QObject, pyqtSignal
import time
import numpy

from data_structures import PyImage

SOCKET = '5556'


def main():
    thread = EventThread()
    thread.start(daemon=True)
    while True:
        try:
            time.sleep(0.01)
        except KeyboardInterrupt:
            thread.stop()
            print('Stopping')
            break


class EventThread(QObject):
    """ Thread that receives events from Micro-Manager and relays them to the main program"""
    xy_stage_position_changed_event = pyqtSignal(tuple)
    stage_position_changed_event = pyqtSignal(float)
    acquisition_started_event = pyqtSignal(object)
    new_image_event = pyqtSignal(PyImage)
    settings_event = pyqtSignal(str, str, str)
    mda_settings_event = pyqtSignal(object)

    def __init__(self):
        super().__init__()

        self.bridge = Bridge(debug=False)

        # Make three sockets that events circle through to alsways have a ready socket
        self.event_sockets = []
        self.num_sockets = 3
        for socket in range(self.num_sockets):
            socket_provider = self.bridge.construct_java_object('org.micromanager.Studio',
                                                                new_socket=True)
            self.event_sockets.append(socket_provider._socket)

        # PUB/SUB
        context = zmq.Context()
        self.socket = context.socket(zmq.SUB)
        self.socket.connect("tcp://localhost:5556")
        self.socket.setsockopt(zmq.RCVTIMEO, 1000)  # Timeout for the recv() function

        self.thread_stop = threading.Event()

        self.topics = ["StandardEvent", "GUIRefreshEvent"]
        for topic in self.topics:
            self.socket.setsockopt_string(zmq.SUBSCRIBE, topic)

    def start(self, daemon=True):
        self.thread = threading.Thread(target=self.main_thread, args=(self.thread_stop, ),
                                       daemon=daemon)
        self.thread.start()

    def stop(self):
        self.thread_stop.set()
        print('Closing socket')

        self.thread.join()

    def main_thread(self, thread_stop):
        instance = 0
        while not thread_stop.wait(0):
            try:
                #  Get the reply.
                reply = str(self.socket.recv())
                topic = re.split(' ', reply)[0][2:]
                message = json.loads(re.split(' ', reply)[1][0:-1])
                socket_num = instance % self.num_sockets
                evt = self.bridge._class_factory.create(message)(
                    socket=self.event_sockets[socket_num],
                    serialized_object=message,
                    bridge=self.bridge)
                # evt = self.bridge._class_factory.create(message)(socket=self.bridge._master_socket
                # , serialized_object=message, bridge=self.bridge)

                eventString = evt.to_string()
                print(eventString)
                if 'ExposureChangedEvent' in eventString:
                    print(evt.get_new_exposure_time())
                elif 'internal.DefaultAcquisitionStartedEvent' in eventString:
                    self.acquisition_started_event.emit(evt)
                elif 'internal.DefaultAcquisitionEndedEvent' in eventString:
                    print('Acquisition Ended')
                elif '.StagePositionChangedEvent' in eventString:
                    print(evt.get_pos())
                    self.stage_position_changed_event.emit(evt.get_pos()*100)
                elif 'XYStagePositionChangedEvent' in eventString:
                    print(evt.get_x_pos())
                    print(evt.get_y_pos())
                    self.xy_stage_position_changed_event.emit((evt.get_x_pos(), evt.get_y_pos()))
                elif 'internal.DefaultNewImageEvent' in eventString:
                    image = evt.get_image()
                    py_image = PyImage(image.get_raw_pixels().reshape([image.get_width(),
                                                                       image.get_height()]),
                                       image.get_coords().get_t(),
                                       image.get_coords().get_c(),
                                       image.get_metadata().get_elapsed_time_ms())
                    self.new_image_event.emit(py_image)
                elif 'pythoneventserver.CustomSettingsEvent' in eventString:
                    self.settings_event.emit(evt.get_device(), evt.get_property(), evt.get_value())
                elif 'pythoneventserver.CustomMDAEvent' in eventString:
                    self.mda_settings_event.emit(evt.get_settings())
                else:
                    print('This event is not known yet')
            except zmq.error.Again:
                pass
        # Thread was stopped, let's also close the socket then
        self.socket.close()


if __name__ == '__main__':
    main()


# ASYNCIO
# import asyncio
# from zmq.asyncio import Context

# ctx = Context

# async def recv():
#     s = ctx.socket(ctx, zmq.SUB)
#     s.bind('tcp://localhost:5556')
#     # s.setsockopt(zmq.SUBSCRIBE, "topic1")
#     s.subscribe(b'')
#     while True:
#         msg = await s.recv_multipart()
#         print('received', msg)
#     s.close()

# loop = asyncio.get_event_loop()
# loop.run_until_complete(recv())
# loop.close()
