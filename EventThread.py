from pycromanager import Bridge
import threading
import re
import zmq
import json
from PyQt5.QtCore import QObject, pyqtSignal

def main():
    thread = EventThread()
    thread.run(daemon=False)

class EventThread(QObject):
    """ Thread that receives events from Micro-Manager and relays them to the main program"""
    xy_stage_position_changed_event = pyqtSignal(tuple)
    stage_position_changed_event = pyqtSignal(float)


    def __init__(self):
        super().__init__()
        self.topics = ["StandardEvent"]


        self.bridge = Bridge()

        #PUB/SUB
        context = zmq.Context()
        self.socket = context.socket(zmq.SUB)
        self.socket.connect("tcp://localhost:5556")
        for topic in self.topics:
            self.socket.setsockopt_string(zmq.SUBSCRIBE, topic)
        self.socket.setsockopt(zmq.RCVTIMEO, 1000)

    def run(self, daemon = True):
        thread = threading.Thread(target=self.main_thread, daemon=daemon)
        thread.start()

    def main_thread(self):
        while True:
            try:
                #  Get the reply.
                reply = str(self.socket.recv())

                topic = re.split(' ', reply)[0][2:]
                message = json.loads(re.split(' ', reply)[1][0:-1])
                evt = self.bridge._class_factory.create(message)(socket=self.bridge._master_socket,
                                                            serialized_object=message, bridge=self.bridge)
                print(evt.to_string())
                if 'org.micromanager.events.ExposureChangedEvent' in evt.to_string():
                    print(evt.get_new_exposure_time())
                elif 'org.micromanager.events.internal.DefaultAcquisitionStartedEvent' in evt.to_string():
                    print(evt.get_datastore().to_string())
                    print(evt.get_settings().interval_ms())
                elif 'org.micromanager.events.internal.DefaultAcquisitionEndedEvent' in evt.to_string():
                    print(evt.get_store().to_string())
                elif 'org.micromanager.events.StagePositionChangedEvent' in evt.to_string():
                    print(evt.get_pos())
                    self.stage_position_changed_event.emit(evt.get_pos()*100)
                elif 'org.micromanager.events.XYStagePositionChangedEvent' in evt.to_string():
                    print(evt.get_x_pos())
                    print(evt.get_y_pos())
                    self.xy_stage_position_changed_event.emit((evt.get_x_pos(), evt.get_y_pos()))
                else:
                    print('This event is not known yet')

            except KeyboardInterrupt:
                print('Closing socket')
                self.socket.close()
                break
            except zmq.error.Again:
                pass

if __name__ == '__main__':
    main()


#ASYNCIO
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
