import asyncio
import websockets
import time
import random
import math

async def hello():
    random.seed(time.time())
    async with websockets.connect("ws://localhost:8080/Arduino") as websocket:
        await websocket.send("Test_1")
        i = 0
        while True:
            current = list()
            voltage = list()
            for j in range(0,10):
                temp_v = 5.0 * math.sin(2*math.pi*100*(i / 10000.0))
                temp_v = temp_v + (random.randint(-100, 100) / 1000.0 )
                temp_c = math.sin(2*math.pi*100*(i / 10000.0) + (0.25 * math.pi))
                temp_c = temp_c + (random.randint(-100, 100) / 1000.0 )
                current.append(temp_c)
                voltage.append(temp_v)
                i += 1

            current = [ str(x) for x in current ]
            voltage = [ str(x) for x in voltage ]
            voltage_str = "v=[" + ','.join(voltage) + "]"
            current_str = "c=[" + ','.join(current) + "]"
            string = voltage_str + ";" + current_str
            print(string)
            await websocket.send(string)
            time.sleep(1)

asyncio.run(hello())
