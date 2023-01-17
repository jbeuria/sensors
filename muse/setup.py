from muselsl import stream, list_muses,record
import multiprocessing as mp
import time
from pylsl import StreamInfo, StreamOutlet
import socket


info = StreamInfo('Markers', 'Markers', 1, 0, 'string', 'myuidw43536')
outlet = StreamOutlet(info)

def sendMarker(marker=[1]):
    #e.g. marker=[1]
    time.sleep(5)
    outlet.push_sample(marker)

def startStream(duration):
    muses = list_muses()
    print(muses[0])
    stream(muses[0]['address'], ppg_enabled=True, acc_enabled=True, gyro_enabled=True)



def recordStream(duration):
    time.sleep(15)
    # Note: an existing Muse LSL stream is required
    record(duration)

    # Note: Recording is synchronous, so code here will not execute until the stream has been closed
    print('Recording has ended')

def recordStream2(duration):
    time.sleep(15)
    s = socket.create_connection(("localhost", 22345))
    s.sendall(b"select all\n")
    s.sendall(b"filename {root:/Users/jb/Development/sensors/muse} {template:exp%n\\%p_block_%b.xdf} {run:2} {participant:P003} {task:MemoryGuided}\n")
    s.sendall(b"start\n")
    time.sleep(duration)
    s.sendall(b"stop\n")
    print('Recording has ended from labrecorder')


#if __name__ == '__main__':
def start():
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

