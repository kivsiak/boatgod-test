import asyncio
from random import randint

import aiopubsub

from boatgod.hub import lora_publisher
from boatgod.nmea2000 import create_rmp_message, create_position_message, create_voltage_message


async def fake_lora_generator():
    while True:
        lora_publisher.publish(aiopubsub.Key('message', 'nmea2000'),
                               create_rmp_message(randint(2000, 2500)))
        # lora_publisher.publish(aiopubsub.Key('message', 'nmea2000'),
        #                        create_position_message(13.165 + randint(1, 100) / 10, 55.11 + randint(1, 100) / 10))
        lora_publisher.publish(aiopubsub.Key('message', 'nmea2000'),
                               create_voltage_message(13.12))

        lora_publisher.publish(aiopubsub.Key('message', 'nmea2000'),
                               create_position_message(43.51567302199084, 16.231514405287953))
        await asyncio.sleep(1)
