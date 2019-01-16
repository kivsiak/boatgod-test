import asyncio

import aiopubsub

from boatgod.hub import lora_publisher
from boatgod.nmea2000 import create_rmp_message, create_voltage_message


class LoraProtocol(asyncio.Protocol):
    VOLTAGE_MULTIPLIER = 1.7636363636363637 / 100
    RPM_CALIBRATION = 1

    def __init__(self):
        self.result = []
        self.inverse = 0x00
        self.state = 0
        self.point = 0
        self.len = 0
        self.crc = 0
        self.transport = None

    def connection_made(self, transport):
        self.transport = transport
        print('port opened', transport)

    def data_received(self, pck):
        for a in pck:
            if a == 0xAA:
                self.result = []
                self.state = 1
                self.point = 0
                self.len = 0
                self.inverse = 0x00
                self.crc = 0
                continue
            if a == 0xBB:
                self.inverse = 0xFF
                continue
            if self.state == 0:
                continue
            b = a ^ self.inverse
            self.inverse = 0
            if self.point == 0:
                self.len = b

            if self.point > self.len:
                if b != (self.crc & 255):
                    self.state = 0
                    continue
                self.on_message(self.result[1:])
            self.crc += b
            self.result.append(b)
            self.point += 1

    def connection_lost(self, exc):
        pass

    def on_message(self, msg):

        cmd = msg[3]
        if cmd == 0x02:  # напряжение оборотыm
            v = int.from_bytes(msg[6:8], "little") * LoraProtocol.VOLTAGE_MULTIPLIER
            rpm = int.from_bytes(msg[4:6], "little") * 60 * LoraProtocol.RPM_CALIBRATION
            lora_publisher.publish(aiopubsub.Key('obj', 'voltage'), v)
            lora_publisher.publish(aiopubsub.Key('obj', 'rpm'), rpm)

            lora_publisher.publish(aiopubsub.Key('message', 'nmea2000'),
                                   create_rmp_message(rpm))

            lora_publisher.publish(aiopubsub.Key('message', 'nmea2000'),
                                   create_voltage_message(v))

        if cmd == 0x03:  # геркон протечка напряжение на батарейке
            lora_publisher.publish(aiopubsub.Key('obj', 'flood'),
                                   dict(water=msg[4],
                                        door=msg[5],
                                        battery=msg[6],
                                        ))
