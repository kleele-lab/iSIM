#%%
from pycromanager import Bridge, core
import pycromanager
import threading
import re
import zmq
import time
from datetime import datetime
import json

topics = ["ExposureChangedEvent", "AcquisitionSequenceStartedEvent", "AcquisitionStartedEvent",
          "DataProviderHasNewImageEvent", "test"]
#%%
bridge = Bridge()
studio = bridge.get_studio()
acquisition = studio.get_acquisition_manager()


#%%
#PUB/SUB
context = zmq.Context()
socket = context.socket(zmq.SUB)

socket.connect("tcp://localhost:5556")  #5556")
for topic in topics:
    socket.setsockopt_string(zmq.SUBSCRIBE, topic)
socket.setsockopt(zmq.RCVTIMEO, 1000)

while True:
    try:
        t1 = time.process_time()
        #  Get the reply.
        reply = str(socket.recv())
        print(reply)

        topic = re.split(' ', reply)[0][2:]
        print(topic)
        print(re.split(' ', reply)[1][0:-1])
        message = json.loads(re.split(' ', reply)[1][0:-1])
        print(message)
        evt = bridge._class_factory.create(message)(socket=bridge._master_socket, serialized_object=message, bridge=bridge)
        print(evt.get_new_exposure_time())


        if topic == "AcquisitionSequenceStartedEvent":
            settings = acquisition.get_acquisition_settings()
        elif topic == "AcquisitionStartedEvent":
            t1 = time.perf_counter()
            eng = acquisition.get_acquisition_engine()
            datastore = eng.get_acquisition_datastore()
            print(time.perf_counter() - t1)



    except KeyboardInterrupt:
        print('Closing socket')
        socket.close()
        break
    except zmq.error.Again:
        pass




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
