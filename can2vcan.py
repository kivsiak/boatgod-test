from functools import partial
from itertools import islice
import datetime
import bitstring
import struct
import time
from time import sleep

import socket

from can import Message


import can

bustype = 'socketcan'
channel = 'vcan0'
bus = can.interface.Bus(channel=channel, bustype=bustype)


def send_data():
    with open("output.CAN", "rb") as canfile:
        messages = iter(partial(canfile.read, 16), b'')
        ids = set()
        # print(header.hex(), decode2(header))
        time = 1
        prev_time_in_ms = 0

        for chunk in islice(messages, 99999999999999999):
            is_service, time_in_minutes, time_in_milliseconds, message_id, message = decode2(chunk)
            dt = time_in_milliseconds - prev_time_in_ms
            # time.sleep(new_time - dt)
            if (dt) < 0: dt = 1
            time += dt

            delta = datetime.timedelta(milliseconds=time)

            prev_time_in_ms = time_in_milliseconds

            date = str(delta)[:-3]

            if len(date) < 8:
                continue

            result = "%s %s %s %s\r\n" % (date, "N" if is_service else "R", message_id, " ".join(chunks(message, 2)))
            msg = Message(arbitration_id=int(message_id, 16), data=list(map(lambda x: int(x, 16), chunks(message, 2))),
                          extended_id=True)
            bus.send(msg)

            sleep(dt / 1000)


if __name__ == "__main__":
    send_data()
