from pycromanager import Bridge, core

import zmq
import time

# if len(sys.argv) > 1:
#     port =  sys.argv[1]
#     int(port)
# print(port)
# context = core.zmq.Context()
# socket = context.socket(core.zmq.REQ)
# socket.connect ("tcp://localhost:%s" % port)



# while True:
#     #  Wait for next request from client
#     message = socket.recv()
#     print("Received request: ", message)
#     time.sleep (1)
#     socket.send("World from %s" % port)

# test_connect = "tcp://localhost:5556"

# ctx = zmq.Context()
# socket = ctx.socket(zmq.SUB)
# socket.connect(test_connect)

# print("Receiving messages on All Topics ...")
# # filter = "XXX"
# # socket.subscribe(filter)
# while True:
#     print("try to receive")
#     objA = socket.recv()
#     print(objA)



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




# msg = socket.recv_json()


# bridge = Bridge(convert_camel_case=False)
# studio = bridge.get_studio()

# events = studio.getEventManager()
# print(dir(events))
# obj = bridge.construct_java_object('com.google.common.eventbus.EventBus') #('java.util.concurrent.Condition')
# obj = bridge.construct_java_object('java.lang.Object', new_socket=True, debug=0)
# print(dir(obj))


# obj.register(events)