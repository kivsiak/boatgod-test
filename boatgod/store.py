import asyncio
import json
import os
import struct

import time

import aiohttp
import aiopubsub
import bitstring
from can import Message

from boatgod.hub import hub
from boatgod.nmea2000 import Iso11783Decode

with open(os.path.dirname(__file__) + "/../pgns.json", "r") as f:
    pgns = json.load(f)["PGNs"]

print("pgn loaded")

import sqlite3

conn = sqlite3.connect(os.path.dirname(__file__) + "/../log.sqlite")

cursor = conn.cursor()

cursor.execute(
    """
        create table  if not exists "data"
        ("time" INT ,
        "pgn" INT,
        "data" BLOB
        )
    """)


def parse(pgn, data):
    result = {
        "id": pgn['PGN'],
        "description": pgn['Description']
    }
    bs = bitstring.BitArray(data)
    for field in pgn['Fields']:
        bits = bs[field["BitOffset"]:field["BitOffset"] + field["BitLength"]]
        result[field['Name']] = bits.intle * float(field.get('Resolution', 1))

    return result


def write_to_database(time, pgn, data):
    cursor.execute("""insert into data values(?,?,?)""", (time, pgn, data))
    conn.commit()


async def store_records():
    print("init store")

    subscriber = aiopubsub.Subscriber(hub, 'store_handler')

    canbus_key = aiopubsub.Key('canbus', 'message', '*')
    # lora_key = aiopubsub.Key('lora', 'obj', '*')
    # subscriber.subscribe(lora_key)
    lora_key = aiopubsub.Key('lora', 'message', 'nmea2000')
    subscriber.subscribe(canbus_key)
    subscriber.subscribe(lora_key)

    depth_date = 0
    lat_lon_date = 0
    engine_time = 0
    voltage_time = 0
    while True:
        key, message = await subscriber.consume()
        pgn, *_ = Iso11783Decode(message.arbitration_id)

        if pgn == 128267:  # depth # latlong
            if depth_date + 3 <= time.time():
                depth_date = time.time()
                write_to_database(time.time(), pgn, message.data)

        if pgn == 129025:
            if lat_lon_date + 3 <= time.time():
                lat_lon_date = time.time()
                write_to_database(time.time(), pgn, message.data)

        if pgn == 127488:
            _, rpm, _, _ = struct.unpack("<bhhb", message.data)
            rpm = rpm / 4

            if rpm > 10 and engine_time + 3 <= time.time():
                engine_time = time.time()
                write_to_database(time.time(), pgn, message.data)

        if pgn == 127508:

            _, voltage, _, _, _ = struct.unpack("<bhhhb", message.data)

            if voltage > 10 and voltage_time + 60 <= time.time():
                voltage_time = time.time()
                write_to_database(time.time(), pgn, message.data)


async def post_data():
    SLEEP = 5

    BOAT_ID = "e6acdc24-2869-4b14-8890-c24ad338c791" #SLAVIA

    # HOST = "http://127.0.0.1:8000/api/datalogs/%s/" % BOAT_ID
    HOST = "https://boatpilot.me/api/datalogs/%s/" % BOAT_ID

    while True:
        async with aiohttp.ClientSession() as session:
            cursor.execute(("""select ROWID, "time", pgn, "data" from data order by "time" limit 1000 """))
            body = ""
            sent = []
            for rowid, dt, pgn, data in cursor.fetchall():
                sent.append([rowid, ])
                body += "%s:%s:%s\n" % (dt, pgn, data.hex())
            try:
                async with session.post(HOST, data=body) as resp:
                    if resp.status == 200:
                        cursor.executemany("""delete from data where ROWID = ?""", sent)
                        conn.commit()
            except aiohttp.ClientError:
                pass

            await asyncio.sleep(SLEEP)
