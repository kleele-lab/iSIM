from pycromanager import Bridge, core
import pycromanager
import threading
import zmq
import time
from datetime import datetime


# context = zmq.Context()
# sockedt = context.socket(zmq.REQ)
# socket.connect("tcp://localhost:5556")  #5556")


# while True:
#     try:
#         t1 = time.process_time()
#         print('Waiting for new event')
#         socket.send_string("Hello")
#         #  Get the reply.
#         message = socket.recv()
#         print(time.process_time() - t1)
#     except KeyboardInterrupt:
#             break



#PUB/SUB
context = zmq.Context()
socket = context.socket(zmq.SUB)
socket.connect("tcp://localhost:5560")  #5556")
topicfilter = "topic1"
socket.setsockopt_string(zmq.SUBSCRIBE, topicfilter)

while True:
    try:
        t1 = time.process_time()
        print('Waiting for new event')
        #  Get the reply.
        message = socket.recv()
        print(message)
        print(datetime.utcnow())
    except KeyboardInterrupt:
        socket.close()
        break




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
