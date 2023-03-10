from muselsl import stream, list_muses,record
import multiprocessing as mp
import time
import os
from pylsl import StreamInfo, StreamOutlet
import socket
from datetime import datetime
now = datetime.now() # current date and time

info = StreamInfo('Markers', 'Markers', 1, 0, 'string', 'myuidw43536')
outlet = StreamOutlet(info)

def sendMarker(marker=[1]):
    #e.g. marker=[1]
    time.sleep(5)
    outlet.push_sample(marker)

def startStream():
    muses = list_muses()
    print(muses[0])
    stream(muses[0]['address'], ppg_enabled=True, acc_enabled=True, gyro_enabled=True)


#This is the CSV export without any marker 
def recordStream(duration,filename=None,type="EEG"):
    time.sleep(15)
    # Note: an existing Muse LSL stream is required
    record(duration=duration,data_source=type,filename=filename)

    # Note: Recording is synchronous, so code here will not execute until the stream has been closed
    print('Recording has ended')

#Labrecorder should be running in the backgroup for recording from labrecorder. 
#this is just a socket connection.

def recordStream2(duration=300,run=1,participant='P001',task="Study"):
    time.sleep(15)

    s = socket.create_connection(("localhost", 22345))
    s.sendall(b"select all\n")
    save_path=os.getcwd()
    s.sendall(bytes("filename {root: %s}"%save_path + "{template:exp%n_%p_block_%b.xdf} {run:run} {participant:participant} {task:task}\n","utf-16"))
    s.sendall(b"filename test.xdf\n")

    s.sendall(b"start\n")

    #sleep for the duration and stop thereafter
    time.sleep(duration)
    s.sendall(b"stop\n")
    print('Recording has ended from labrecorder')


def start():
    if __name__ == '__main__':
        p1 = mp.Process(name='stream', target=startStream)
        #p2 = mp.Process(name='markers', target=sendMarker)
        #p3 = mp.Process(name='record', target=recordStream,args=(120,))
        p4 = mp.Process(name='record2', target=recordStream2,args=(120,))                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                         

        p1.start()
        #p2.start()
        #p3.start()
        p4.start()

        p1.join()
        #p2.join()
        #p3.join()
        p4.join()


start()
# Note: Streaming is synchronous, so code here will not execute until after the stream has been closed
print('Stream has ended')

