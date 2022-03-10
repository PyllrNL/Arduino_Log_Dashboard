import asyncio
import websockets
import time
import random
import math
import string

import base64
import msgpack
i = 1

def construct_data(samples, sample_freq, v_peak, c_peak):
    global i
    current = list()
    voltage = list()

    for j in range(0, samples):
        noise = random.randint(-100, 100) / 2.5
        temp_v = (v_peak * math.sin(2*math.pi*(25.0 / sample_freq) * i)) + noise
        temp_c =  c_peak * math.sin(2*math.pi*(25.0 / sample_freq)*i + (0.5 * math.pi))
        temp_c += (c_peak/2) * math.sin(2*math.pi*(123.0 / sample_freq)*i + (0.5 * math.pi))
        voltage.append(int(temp_v))
        current.append(temp_c)
        i = i + 1
    return (voltage, current)

def get_rms_values(samples):
    voltage = list()
    current = list()
    for i in range(0, samples):
        v_peak = random.randint(320, 322)
        c_peak = random.randint(10, 10) / 10.0
        v, c = construct_data(101, v_peak, c_peak)
        rms_voltage = 0
        rms_current = 0
        for i in range(0, len(v)):
            rms_voltage += v[i] * v[i]
            rms_current += c[i] * c[i]
        rms_voltage = rms_voltage / len(v)
        rms_current = rms_current / len(c)
        rms_voltage = math.sqrt(rms_voltage)
        rms_current = math.sqrt(rms_current)
        voltage.append(rms_voltage)
        current.append(rms_current)
    return (voltage, current)


async def hello():
    random.seed(time.time())
    async with websockets.connect("ws://167.71.68.242:80/device/03pwbIIosvgLQhC_USUHmN6Iz-86xyY_X7noo-jksMc") as websocket:
        response = await websocket.recv()
        while True:
            raw = construct_data(100, 777, 322, 1.0)
            packed = msgpack.packb([raw[0], raw[1]], use_bin_type=True)
            encoded = base64.b64encode(packed)
            await websocket.send(encoded)
            await asyncio.sleep(1)

asyncio.run(hello())
