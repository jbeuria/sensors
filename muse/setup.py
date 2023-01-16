from muselsl import stream, list_muses,record
import multiprocessing as mp
import threading as th
import time

def startStream():
    muses = list_muses()
    print(muses[0])
    stream(muses[0]['address'], ppg_enabled=True, acc_enabled=True, gyro_enabled=True)



def recordStream(duration):
    time.sleep(15)
    # Note: an existing Muse LSL stream is required
    record(duration)

    # Note: Recording is synchronous, so code here will not execute until the stream has been closed
    print('Recording has ended')

'''
pools=mp.Pool(2)
pools[0].map(startStream)
pools[1].map(recordData,
'''

if __name__ == '__main__':
    p1 = mp.Process(name='stream', target=startStream)
    p2 = mp.Process(name='record', target=recordStream,args=(120,))
    p1.start()
    p2.start()
    p1.join()
    p2.join()


'''
p1 = th.Thread(name='stream', target=startStream)
p2 = th.Thread(name='record', target=recordStream,args=(120,))
p1.start()
p2.start()
p1.join()
p2.join()
'''

# Note: Streaming is synchronous, so code here will not execute until after the stream has been closed
print('Stream has ended')