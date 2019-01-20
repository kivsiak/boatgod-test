from functools import partial
from itertools import islice
import datetime
import bitstring
import struct
import time
from time import sleep

import socket

from can import Message


def chunks(l, n):
    """Yield successive n-sized chunks from l."""
    for i in range(0, len(l), n):
        yield l[i:i + n]


def decode(msg: bytes):
    '''

    :param msg 16 bytes:
    :return: service_info, timeoffest, messaege_id, data =
    '''

    service, msg = msg[:2], msg[2:]
    time_of_record_in_miliseconds, msg = int.from_bytes(msg[:2], byteorder="little", signed=False), msg[2:]
    message_id, message = msg[:4], msg[4:]
    bs = bitstring.BitArray(service)
    bs.reverse()
    time_of_record_in_miutes = bs[:10]
    minutes = int(time_of_record_in_miutes.bin, 2)

    return bs.bin, int(bs[10]), bs[14], bs[15], int(bs[11:14].bin, 2), str(
        datetime.timedelta(minutes=minutes, milliseconds=time_of_record_in_miliseconds))[:-3], bitstring.BitArray(
        message_id).bin, message.hex()


def decode2(msg: bytes):



    service, msg = msg[:2], msg[2:]
    time_of_record_in_miliseconds, msg = int.from_bytes(msg[:2], byteorder="little", signed=False), msg[2:]
    message_id, message = msg[:4], msg[4:]



    ms = bitstring.BitArray(message_id[::-1])
    ms_reversed = bitstring.BitArray(message_id)


    service = bitstring.BitArray(service[::-1])[::-1]

    is_service = service[14]
    is_29 = service[15]
    data_len = int(service[11:14].bin,2)+1
    time_in_minutes = int(service[0:10].bin, 2)


    return  is_service, time_in_minutes, time_of_record_in_miliseconds, ms.hex, str(message.hex())[:data_len*2]

import  can

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
            if(dt)<0: dt =1
            time+= dt

            delta = datetime.timedelta(milliseconds = time)


            prev_time_in_ms = time_in_milliseconds

            
            date =str(delta)[:-3]

            if len(date)< 8:
                continue


            result = "%s %s %s %s\r\n" %( date, "N" if is_service else "R", message_id, " ".join(chunks(message,2)))
            msg = Message(arbitration_id=int(message_id,16), data=list(map(lambda  x: int(x, 16), chunks(message,2))), extended_id=True)
            bus.send(msg)
            print(msg)
            sleep(dt/1000)
        



if __name__ == "__main__":
    send_data()


