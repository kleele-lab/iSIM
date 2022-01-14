from pycromanager import Bridge, core, Acquisition
import threading
import re
import zmq
import json
from PyQt5.QtCore import QObject, pyqtSignal
import time

from data_structures import PyImage, MMSettings

SOCKET = '5556'

class EventThread(QObject):
    """ Thread that receives events from Micro-Manager and relays them to the main program"""
    xy_stage_position_changed_event = pyqtSignal(tuple)
    stage_position_changed_event = pyqtSignal(float)
    acquisition_started_event = pyqtSignal(object)
    acquisition_ended_event = pyqtSignal(object)
    new_image_event = pyqtSignal(PyImage)
    settings_event = pyqtSignal(str, str, str)
    mda_settings_event = pyqtSignal(object)

    def __init__(self):
        super().__init__()

        self.bridge = Bridge(debug=False)

        # Make sockets that events circle through to always have a ready socket
        self.event_sockets = []
        self.num_sockets = 5
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

        self.topics = ["StandardEvent", "GUIRefreshEvent", "ImageEvent"]
        for topic in self.topics:
            self.socket.setsockopt_string(zmq.SUBSCRIBE, topic)

        # Record times for events that we receive twice
        self.last_acq_started = time.perf_counter()
        self.last_custom_mda = time.perf_counter()

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
            instance = instance + 1 if instance < 100 else 0
            try:
                #  Get the reply.
                reply = str(self.socket.recv())
                # topic = re.split(' ', reply)[0][2:]
                message = json.loads(re.split(' ', reply)[1][0:-1])
                socket_num = instance % self.num_sockets
                pre_evt = self.bridge._class_factory.create(message)

                evt = pre_evt(
                    socket=self.event_sockets[socket_num],
                                                            serialized_object=message,
                                                            bridge=self.bridge)

                eventString = message['class'].split(r'.')[-1]
                print(eventString, ' ', time.perf_counter())
                if 'ExposureChangedEvent' in eventString:
                    print(evt.get_new_exposure_time())
                elif 'DefaultAcquisitionStartedEvent' in eventString:
                    if time.perf_counter() - self.last_acq_started > 0.2:
                        self.acquisition_started_event.emit(evt)
                        print('ACQ started Event emitted ', time.perf_counter())
                    else:
                        print('SKIPPED')
                    self.last_acq_started = time.perf_counter()
                elif 'DefaultAcquisitionEndedEvent' in eventString:
                    self.acquisition_ended_event.emit(evt)
                    print('Acquisition Ended')
                elif 'StagePositionChangedEvent' in eventString:
                    print(evt.get_pos())
                    self.stage_position_changed_event.emit(evt.get_pos()*100)
                elif 'XYStagePositionChangedEvent' in eventString:
                    print(evt.get_x_pos())
                    print(evt.get_y_pos())
                    self.xy_stage_position_changed_event.emit((evt.get_x_pos(), evt.get_y_pos()))
                elif 'DefaultNewImageEvent' in eventString:
                    # image = self.predef_events.default_new_image_event.get_image()
                    image = evt.get_image()
                    py_image = PyImage(image.get_raw_pixels().reshape([image.get_width(),
                                                                       image.get_height()]),
                                       image.get_coords().get_t(),
                                       image.get_coords().get_c(),
                                       image.get_metadata().get_elapsed_time_ms())
                                    #  0) # no elapsed time
                    self.new_image_event.emit(py_image)
                elif 'CustomSettingsEvent' in eventString:
                    self.settings_event.emit(evt.get_device(), evt.get_property(), evt.get_value())
                elif 'CustomMDAEvent' in eventString:
                    if time.perf_counter() - self.last_custom_mda > 0.2:
                        settings = evt.get_settings()
                        # print(dir(settings))
                        settings = MMSettings(java_settings=settings)
                        self.mda_settings_event.emit(settings)
                    else:
                        print('SKIPPED')
                    self.last_custom_mda = time.perf_counter()



                else:
                    print('This event is not known yet')
            except zmq.error.Again:
                pass
        # Thread was stopped, let's also close the socket then
        self.socket.close()




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

if __name__ == '__main__':
    main()