import datetime

import aiopubsub

from boatgod.hub import hub


# TODO упросить
def message_to_yachd_raw(mesg):
    field_strings = [datetime.datetime.fromtimestamp(mesg.timestamp).strftime("%H:%M:%S.%f")[:-3]]

    field_strings.append("R")

    if mesg.id_type:
        # Extended arbitrationID
        arbitration_id_string = "{0:08x}".format(mesg.arbitration_id)
    else:
        arbitration_id_string = "{0:04x}".format(mesg.arbitration_id)
    field_strings.append(arbitration_id_string)

    data_strings = []
    if mesg.data is not None:
        for index in range(0, min(mesg.dlc, len(mesg.data))):
            data_strings.append("{0:02x}".format(mesg.data[index]))

    if data_strings.__len__() > 8:
        data_strings = data_strings[:8]
    if data_strings:  # if not empty
        field_strings.append(" ".join(data_strings).strip())
    else:
        field_strings.append(" " * 24)

    x = " ".join(field_strings)
    x += "\r\n"

    return x


async def handler(reader, writer):
    subscriber = aiopubsub.Subscriber(hub, 'rawhandler')
    canbus_key = aiopubsub.Key('canbus', 'message', '*')
    lora_key = aiopubsub.Key('lora', 'message', 'nmea2000')
    subscriber.subscribe(lora_key)
    subscriber.subscribe(canbus_key)
    print("open_connection")
    try:
        while True:
            key, message = await subscriber.consume()
            data = message_to_yachd_raw(message)
            # print(data)
            writer.write(data.encode("utf-8"))
            await writer.drain()
    except ConnectionError:
        subscriber.unsubscribe(lora_key)
        # subscriber.unsubscribe(canbus_key)
        print("Connection closed")
