import datetime

import bitstring


def chunks(l, n):
    """Yield successive n-sized chunks from l."""
    for i in range(0, len(l), n):
        yield l[i:i + n]


def decode(msg: bytes):
    """

    :param msg 16 bytes:
    :return: service_info, timeoffest, messaege_id, data =
    """

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
    data_len = int(service[11:14].bin, 2) + 1
    time_in_minutes = int(service[0:10].bin, 2)

    return is_service, time_in_minutes, time_of_record_in_miliseconds, ms.hex, str(message.hex())[:data_len * 2]
