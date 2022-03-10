import asyncio
import websockets
import time
import random
import math
import string

import base64
import msgpack
i = 0

def construct_data(samples):
    global i
    current = list()
    voltage = list()
    for j in range(0, samples):
        temp_v = 5.0 * math.sin(2*math.pi*141*( i / 4000.0))
        temp_v += math.sin(2*math.pi*300*( i / 4000.0))
        #temp_v += (random.randint(-100, 100) / 250.0)
        temp_c = 0.01 * math.sin(2*math.pi*57*((i) / 4000.0) + (0.5 * math.pi))
        temp_c += 0.005 * math.sin(2*math.pi*100*((i) / 4000.0))
        voltage.append(temp_v)
        current.append(temp_c)
        i = i + 1
    return (voltage, current)


async def hello():
    random.seed(time.time())
    async with websockets.connect("ws://167.71.68.242:80/device/12345") as websocket:
        response = await websocket.recv()
        while True:
            raw = construct_data(100)
            data = list()
            data.append(raw[0])
            data.append(raw[1])
            packed = msgpack.packb(data, use_bin_type=True)
            encoded = base64.b64encode(packed)
            await websocket.send(encoded)
            await asyncio.sleep(1)

asyncio.run(hello())
