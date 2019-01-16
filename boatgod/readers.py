import asyncio
import datetime
from functools import partial
from itertools import islice

import aiopubsub
from can import Message
import can
import os
from boatgod.hub import canbus_publisher
from boatgod.nmea2000 import Iso11783Encode
from boatgod.utils import decode2, chunks


async def boatgod_reader():
    print("read from boatgod dump")
    pub_key = aiopubsub.Key('message', 'file')
    while True:
        with open(os.path.dirname(__file__) + "/../dump.dat", ) as canfile:

            ids = set()
            time = 1
            prev_time = 0
            engine = False


            for line in canfile.readlines():

                timestamp, pgn, data = line.split(":")
                timestamp = float(timestamp)
                pgn = int(pgn)
                # if pgn  == 127488:
                #     engine = True
                #
                # if pgn != 129025:
                #     continue


                dt = timestamp - prev_time
                if dt < 0:
                    dt = 1
                time += dt
                delta = datetime.timedelta(seconds=time)
                prev_time = timestamp
                date = str(delta)[:-3]
                if len(date) < 8:
                    continue
                data = data.strip()
                msg = Message(arbitration_id=Iso11783Encode(pgn, 0, 0, 0),
                              data=list(map(lambda x: int(x, 16), chunks(data.encode(), 2))),
                              extended_id=True)


                canbus_publisher.publish(pub_key, msg)
                # print(dt)
                if(dt > 1000):
                    continue

                await asyncio.sleep(dt/10)


async def canbus_reader(channel, bustype):
    # чтение сокета блокирующее. вынести в отдельный процесс и гнать через zmq? через тред?
    print("read from canbus")

    while True:
        try:
            pub_key = aiopubsub.Key('message', 'socket')
            bus = can.interface.Bus(channel=channel, bustype=bustype)
            while True:
                msg = bus.recv()
                canbus_publisher.publish(pub_key, msg)
                await asyncio.sleep(0)
        except can.CanError:
            await  asyncio.sleep(3)


async def canfile_reader():
    print("read from canfile")
    pub_key = aiopubsub.Key('message', 'file')
    while True:
        with open("../output.CAN", "rb") as canfile:
            messages = iter(partial(canfile.read, 16), b'')
            ids = set()
            time = 1
            prev_time_in_ms = 0

            for chunk in islice(messages, 99999999999999999):
                is_service, time_in_minutes, time_in_milliseconds, message_id, message = decode2(chunk)
                dt = time_in_milliseconds - prev_time_in_ms
                if dt < 0:
                    dt = 1
                time += dt
                delta = datetime.timedelta(milliseconds=time)
                prev_time_in_ms = time_in_milliseconds
                date = str(delta)[:-3]
                if len(date) < 8:
                    continue
                msg = Message(arbitration_id=int(message_id, 16),
                              data=list(map(lambda x: int(x, 16), chunks(message, 2))),
                              extended_id=True)


                canbus_publisher.publish(pub_key, msg)
                await asyncio.sleep(dt / 1000)
