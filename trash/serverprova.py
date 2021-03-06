# this script accept a JSON, as a string, and send a string that contains an integer
# that indicates the speed

import json
import socket
from DetectorHandler import DetectorHandler
import cv2
import threading
import constants
import Planner

planner = Planner.Planner()

running = True

TCP_IP = "192.168.1.86"
TCP_PORT = 1931
s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)  # IP .4 & TCP
# this should prevent errors of "already in use"
s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
s.bind((TCP_IP, TCP_PORT))  # bind socket

BUFFER_SIZE = 512  # BUFFER SIZE - da controllare se aumentare o diminuire
# This function takes an int argument called backlog, which specifies the
# maximum number of  connections that are kept waiting if the application is
# already busy.
s.listen(1)
cap = cv2.VideoCapture('rtsp://@192.168.1.245/live/ch00_0', cv2.CAP_FFMPEG)


class AcquireFrames(threading.Thread):
    def __init__(self):
        threading.Thread.__init__(self)

    def run(self):
        global cap
        global ret
        global running
        while running:
            ret = cap.grab()


frames_grabber = AcquireFrames()

frames_grabber.start()

detector_handler = DetectorHandler()

cv2.namedWindow('mask')
cv2.namedWindow('img')


print "Listening started"
try:
    while True:  # wait connection
        conn, addr = s.accept()  # accept connection
        # message from the client
        message = conn.recv(BUFFER_SIZE)

        print message, '\n'

        if not message:
            print "There is no message"
            break

        ret, frame = cap.retrieve(ret)

        input_dictionary = json.loads(message)

        leftObstacle = input_dictionary["leftObstacle"] == 0
        frontObstacle = input_dictionary["frontObstacle"] == 0
        rightObstacle = input_dictionary["rightObstacle"] == 0

        if not leftObstacle and not rightObstacle and not frontObstacle:
            if frame is not None:
                detector_handler.find_target(frame)
                if detector_handler.target:
                    server_message = detector_handler.do_action()
                else:
                    server_message = planner.plan(leftObstacle, rightObstacle)
                    server_message = constants.FORWARD  # planner.plan(leftObstacle, rightObstacle)

                cv2.imshow('img', frame)
            else:
                server_message = constants.FORWARD
        elif leftObstacle and rightObstacle:
            server_message = constants.BACKWARD_RIGHT
        elif leftObstacle:
            server_message = constants.TURN_RIGHT_MICRO
        elif rightObstacle:
            server_message = constants.TURN_LEFT_MICRO
        else:
            server_message = constants.BACKWARD_LEFT

        conn.send(str(server_message))

        cv2.waitKey(1)
except KeyboardInterrupt:
    print "Shutting down"
    running = False
    s.close()
running = False
cap.release()
cv2.destroyAllWindows()
