import time
from simple_facerec import SimpleFacerec
from threading import Thread
import cv2
import pandas as pd
import pyfirmata


class WebcamStream:

    def __init__(self, stream_id=0):
        self.stream_id = stream_id

        self.vcap = cv2.VideoCapture(self.stream_id)
        self.vcap.set(cv2.CAP_PROP_FOURCC, cv2.VideoWriter_fourcc('M', 'J', 'P', 'G'))
        self.vcap.set(cv2.CAP_PROP_FPS, 60)
        self.vcap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
        self.vcap.set(cv2.CAP_PROP_FRAME_HEIGHT, 400)
        if self.vcap.isOpened() is False:
            print("[Exiting]: Error accessing webcam stream.")
            exit(0)
        fps_input_stream = int(self.vcap.get(5))  # hardware fps
        print("FPS of input stream: {}".format(fps_input_stream))


        self.grabbed, self.frame = self.vcap.read()
        if self.grabbed is False:
            print('[Exiting] No more frames to read')
            exit(0)

        self.stopped = True

        self.t = Thread(target=self.update, args=())
        self.t.daemon = True

    def start(self):
        self.stopped = False
        self.t.start()


    def update(self):
        while True:
            if self.stopped is True:
                break
            self.grabbed, self.frame = self.vcap.read()
            if self.grabbed is False:
                print('[Exiting] No more frames to read')
                self.stopped = True
                break
        self.vcap.release()


    def read(self):
        return self.frame


    def stop(self):
        self.stopped = True



sfr = SimpleFacerec()
sfr.load_encoding_images("images/")
cap = WebcamStream(0)
cap.start()


cap2 = WebcamStream(1)
cap2.start()


df = {"Name": ['Pulak', 'Sameep', 'Sachit', 'Dheirya'],
      "Attendance": ['Absent', 'Absent', 'Absent', 'Absent'],
      "Binary": ["0", "0", "0", "0"],
      "Time Entered":['N/A', 'N/A', 'N/A', 'N/A'],
      "Time Exited":['N/A', 'N/A', 'N/A', 'N/A'],
      "Time in Class":['N/A', 'N/A', 'N/A', 'N/A']}
arduino = pyfirmata.Arduino('COM15')
led = arduino.get_pin('d:5:o')


def turn_on(led):
    led.write(1)
su2 = 0
su = 0
ptime = 0
while True:
    f = cap.read()
    f2 = cap2.read()
    face_locations2, face_name2 = sfr.detect_known_faces(f2)
    face_locations, face_name = sfr.detect_known_faces(f)
    ctime = time.time()
    fps = 1/(ctime-ptime)
    ptime = ctime
    cv2.putText(f, str(int(fps)), (100, 20), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)

    for face_loc2, name2 in zip(face_locations2, face_name2):
        top2, left2, bottom2, right2 = face_loc2[0], face_loc2[1], face_loc2[2], face_loc2[3]
        cv2.rectangle(f2, (left2, top2), (right2, bottom2), (0,255,0), 2)
        cv2.putText(f, name2, (left2, top2 - 10), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
        print(bottom2, left2)
        if name2 != 'Unkown' and left2 > 590:
            inc = 0
            for i in df['Name']:
                if i == name2:
                    df['Time Exited'][inc] = str(time.ctime())[11:16]
                    df['Binary'][inc] = "0"
                    print('exit successful')
                    temp = pd.DataFrame(df)
                    for rem1 in df['Binary']:
                        print(rem1)
                        su2 = su2 + int(rem1)
                        print(su2)
                        if su2 == 0:
                            led.write(0)
                            print('lights off')
                else:
                    inc += 1


    for face_loc, name in zip(face_locations, face_name):
        top, left, bottom, right = face_loc[0], face_loc[1], face_loc[2], face_loc[3]
        cv2.rectangle(f, (left, top), (right, bottom), (0, 255, 0), 2)
        cv2.putText(f, name, (left, top-10), cv2.FONT_HERSHEY_SIMPLEX, 1, (0,255, 0), 2)
        # print(bottom, right)
        if name!='Unkown' and right<50:
            inc = 0
            for i in df['Name']:
                if i == name:
                    df['Time Entered'][inc] = str(time.ctime())[11:16]
                    df['Attendance'][inc] = 'Present'
                    df['Binary'][inc] = "1"
                    print('present')
                    temp = pd.DataFrame(df)
                    for rem in df['Binary']:
                        su = su + int(rem)
                        print(su)
                        if su>0:
                            turn_on(led)
                            print('lights on')
                else:
                    inc += 1
    delay = 0.03
    time.sleep(delay)
    cv2.imshow('f', f)
    cv2.imshow('f2', f2)
    key = cv2.waitKey(1)
    if key==27:


        exc = pd.DataFrame(df)
        exc.to_csv('Attendance.csv')
        break


cap.stop()
cv2.destroyAllWindows()