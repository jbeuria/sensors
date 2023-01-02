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

## UUID for Request of PMD Stream ##
#ACC
PMD_WRITE2 = bytearray([0x02,0x02,0x00, 0x01,0x34,0x00,0x01,0x01,0x10,0x00,0x02,0x01,0x08, 0x00, 0x04, 0x01, 0x03 ])
#PPG
PMD_WRITE1 = bytearray([0x02, 0x01, 0x00, 0x01, 0x34, 0x00, 0x01, 0x01, 0x10, 0x00, 0x02, 0x01, 0x08, 0x00, 0x04, 0x01, 0x03])
#ECG
PMD_WRITE0 = bytearray([0xF0,0x01,0x00,0x00,0x00,0x00,0x01,0x82,0x00,0x01,0x01,0x0E,0x00])

ECG_DATA = 0x00
PPG_DATA = 0x01
ACC_DATA = 0x02


## Keyboard Interrupt Handler
def keyboardInterrupt_handler(signum, frame):
    print("  key board interrupt received...")
    print("----------------Recording stopped------------------------")


## Bit conversion of the Hexadecimal stream
def data_conv(sender, data):
    print("Raw data:", data,"\n",list(data))
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

    
    att_read = await client.read_gatt_char(PMD_CONTROL)
    print(att_read)

    await client.start_notify(PMD_DATA, data_conv)
    # await client.write_gatt_char(PMD_CONTROL, ACC_WRITE)  #=====================
    resp=await client.write_gatt_char(PMD_CONTROL, bytearray([0x02,0x03]),response=True)  #=====================

    #att_read = await client.read_gatt_char(PMD_DATA)
    #print(att_read)

    #resp=await client.write_gatt_char(PMD_CONTROL, PMD_WRITE1,response=True)  #=====================
    ## stream started
    #await client.start_notify(PMD_DATA, data_conv)

    #resp=await client.write_gatt_char(PMD_CONTROL,PMD_WRITE1, )
    print(resp)
    print("Collecting data...")

    #plt.show()

    ## Stop the stream once data is collected
    
    await aioconsole.ainput('Running: Press a key to quit \n')
    #await client.stop_notify(PMD_DATA)
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
