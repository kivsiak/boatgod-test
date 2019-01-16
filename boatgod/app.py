import asyncio
import platform

import serial_asyncio

from boatgod.generators import fake_lora_generator
from boatgod.lora import LoraProtocol
from boatgod.readers import canbus_reader, canfile_reader, boatgod_reader
from boatgod.rawserver import handler
from boatgod.store import store_records, post_data

if __name__ == '__main__':
    loop = asyncio.get_event_loop()
    # asyncio.ensure_future(store_records())
    # asyncio.ensure_future(post_data())
    rawserver_coro = asyncio.start_server(handler, "0.0.0.0", 1456, loop=loop)
    server = loop.run_until_complete(rawserver_coro)
    try:
        # if platform.system() == "Linux":
        #     lora_coro = serial_asyncio.create_serial_connection(loop, LoraProtocol, '/dev/ttyS1', baudrate=115200)
        #     loop.run_until_complete(l sora_coro)
        #     bustype = 'socketcan'
        #     channel = 'can0'
        #     loop.run_until_complete(canbus_reader(channel, bustype))
        # else:
            # loop.run_until_complete(fake_lora_generator())
        # loop.run_until_complete(canfile_reader())
        loop.run_until_complete(boatgod_reader())
        loop.run_forever()
    except KeyboardInterrupt:
        print("closing")
        server.close()
        loop.run_until_complete(server.wait_closed())
        loop.close()
