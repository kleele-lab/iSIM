from pycromanager import Bridge, core

import zmq
import time

context = zmq.Context()
socket = context.socket(zmq.REQ)
socket.connect("tcp://localhost:5556")  #5556")


while True:
    try:
        t1 = time.process_time()
        print('Waiting for new event')
        socket.send_string("Hello")
        #  Get the reply.
        message = socket.recv()
        print(time.process_time() - t1)
    except KeyboardInterrupt:
            break
