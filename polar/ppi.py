import asyncio
import math
import os
import signal
import aioconsole 
import sys
import time

import pandas as pd
from bleak import BleakClient
from bleak.uuids import uuid16_dict
import matplotlib.pyplot as plt
import matplotlib

""" Predefined UUID (Universal Unique Identifier) mapping are based on Heart Rate GATT service Protocol that most
Fitness/Heart Rate device manufacturer follow (Polar H10 in this case) to obtain a specific response input from 
the device acting as an API """

uuid16_dict = {v: k for k, v in uuid16_dict.items()}

## This is the device MAC ID, please update with your device ID
ADDRESS = '9F1793AB-9B0E-3AFC-AF1A-65013849B8CF' #'A0:9E:1A:A2:DC:59'

## UUID for model number ##
MODEL_NBR_UUID = "00002a24-0000-1000-8000-00805f9b34fb"
## UUID for manufacturer name ##
MANUFACTURER_NAME_UUID = "0000{0:x}-0000-1000-8000-00805f9b34fb".format(
    uuid16_dict.get("Manufacturer Name String")
)

## UUID for battery level ##
BATTERY_LEVEL_UUID = "0000{0:x}-0000-1000-8000-00805f9b34fb".format(
    uuid16_dict.get("Battery Level")
)

## UUID for connection establsihment with device ##
PMD_SERVICE = "FB005C80-02E7-F387-1CAD-8ACD2D8DF0C8"

## UUID for Request of stream settings ##
PMD_CONTROL = "FB005C81-02E7-F387-1CAD-8ACD2D8DF0C8"

## UUID for Request of start stream ##
PMD_DATA = "FB005C82-02E7-F387-1CAD-8ACD2D8DF0C8"


#Verity Sense Stream Settings
PPG_STREAM=bytearray([0x02, 0x01, 0x00, 0x01, 0x87, 0x00, 0x01, 0x01, 0x16, 0x00, 0x04, 0x01, 0x04])
PPI_STREAM=bytearray([0x02, 0x03])
ACC_STREAM=bytearray([0x02,0x02,0x00, 0x01,0x34,0x00,0x01,0x01,0x10,0x00,0x02,0x01,0x08, 0x00, 0x04, 0x01, 0x03 ])


ECG_DATA = 0x00
PPG_DATA = 0x01
ACC_DATA = 0x02


## Keyboard Interrupt Handler
def keyboardInterrupt_handler(signum, frame):
    print("  key board interrupt received...")
    print("----------------Recording stopped------------------------")


## Bit conversion of the Hexadecimal stream
def data_conv_simple(sender, data):
    print("Raw data:", data,"\n",list(data))
    with open("test.txt", "w") as f:
        f.write(str(data))

def data_conv(sender, data):
    #print("Raw data:", data)
    if data[0] == 0x03: # PPI data
        timestamp = convert_to_unsigned_long(data, 1, 8)
        frame_type = data[9]
        resolution = (frame_type + 1) * 8
        step = math.ceil(resolution / 8.0)
        samples = data[10:]
        offset = 0
        step=6
        while offset < len(samples):
            bpm = int.from_bytes(samples[offset:offset+1], byteorder="little", signed=True)
            ppi= int.from_bytes(samples[offset+1:offset+3], byteorder="little", signed=True)
            ppi_error=int.from_bytes(samples[offset+3:offset+5], byteorder="little", signed=True)
            ppi_flag=int.from_bytes(samples[offset+6:offset+7], byteorder="little", signed=True)
            offset += step

            print(bpm,ppi,ppi_error,ppi_flag)
    with open("test.txt", "w") as f:
        f.write(str(data))

def convert_array_to_signed_int(data, offset, length):
    return int.from_bytes(
        bytearray(data[offset : offset + length]), byteorder="little", signed=True,
    )


def convert_to_unsigned_long(data, offset, length):
    return int.from_bytes(
        bytearray(data[offset : offset + length]), byteorder="little", signed=False,
    )


async def getSettings(client):
    stream_requests=[]
    def notification_handler(sender, data):
            #print(list(data))

            print(', '.join('{:02x}'.format(x) for x in data))

    await client.start_notify(PMD_CONTROL,  notification_handler)

    PPG_SETTING = bytearray([0x01, #get settings
                            0x01]) #type PPG
    ECG_SETTING = bytearray([0x01, 0x00])
    ACC_SETTING = bytearray([0x01, 0x02])
    PPI_SETTING = bytearray([0x01, 0x03])
    GYO_SETTING = bytearray([0x01, 0x05])
    MAG_SETTING = bytearray([0x01, 0x06])

    print('\nECG Settings:')
    await client.write_gatt_char(PMD_CONTROL,ECG_SETTING, response=True)

    print('\nPPG Settings:')
    await client.write_gatt_char(PMD_CONTROL,PPG_SETTING, response=True)

    print('\nPPI Settings:')
    await client.write_gatt_char(PMD_CONTROL,PPI_SETTING, response=True)

    print('\nACC Settings:')
    await client.write_gatt_char(PMD_CONTROL,ACC_SETTING, response=True)

    print('\nGYO Settings:')
    await client.write_gatt_char(PMD_CONTROL,GYO_SETTING, response=True)

    print('\nMAG Settings:')
    await client.write_gatt_char(PMD_CONTROL,MAG_SETTING, response=True)

    await client.stop_notify(PMD_CONTROL)

    return stream_requests




## Aynchronous task to start the data stream for ECG ##
async def run(client, debug=False):

    ## Writing chracterstic description to control point for request of UUID (defined above) ##

    await client.is_connected()
    print("---------Device connected--------------")

    model_number = await client.read_gatt_char(MODEL_NBR_UUID)
    print("Model Number: {0}".format("".join(map(chr, model_number))))

    manufacturer_name = await client.read_gatt_char(MANUFACTURER_NAME_UUID)
    print("Manufacturer Name: {0}".format("".join(map(chr, manufacturer_name))))

    battery_level = await client.read_gatt_char(BATTERY_LEVEL_UUID)
    print("Battery Level: {0}%".format(int(battery_level[0])))

    def notification_handler(sender, data):
            print(', '.join('{:02x}'.format(x) for x in data))
    
    await getSettings(client)
    #HR_UUID = "00002A37-0000-1000-8000-00805F9B34FB"
    #await client.start_notify(HR_UUID,data_conv_simple)
    
    await client.start_notify(PMD_DATA, data_conv)
    await client.write_gatt_char(PMD_CONTROL, PPI_STREAM,response=True)
    #'''
    print("Collecting data...")

    ## Stop the stream once data is collected
    await aioconsole.ainput('Running: Press a key to quit \n')
    await client.stop_notify(PMD_DATA)
    print("Stopping data...", flush=True)
    print("[CLOSED] application closed.", flush=True)
    sys.exit(0)


async def main():
    try:
        async with BleakClient(ADDRESS) as client:
            signal.signal(signal.SIGINT, keyboardInterrupt_handler)
            tasks = [
                asyncio.ensure_future(run(client, True)),
            ]

            await asyncio.gather(*tasks)
    except Exception as error:
        print(error)
        #pass


if __name__ == "__main__":
    print('Reading from Polar Band ....')
    os.environ["PYTHONASYNCIODEBUG"] = str(1)
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    loop.run_until_complete(main())
