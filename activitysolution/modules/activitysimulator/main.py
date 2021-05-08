# Copyright (c) Microsoft. All rights reserved.
# Licensed under the MIT license. See LICENSE file in the project root for
# full license information.

import time
import os
import sys
import csv
import json
import asyncio
from six.moves import input
import threading
from datetime import datetime
from azure.iot.device.aio import IoTHubModuleClient
from azure.iot.device import Message

async def main():
    try:
        if not sys.version >= "3.5.3":
            raise Exception( "The sample requires python 3.5.3+. Current version of Python: %s" % sys.version )
        print ( "IoT Hub Client for Python" )

        # The client object is used to interact with your Azure IoT hub.
        module_client = IoTHubModuleClient.create_from_edge_environment()

        await module_client.connect()

        async def send_async_message(i):
            # print(i)
            msg = Message(json.dumps(i))
            await module_client.send_message_to_output(msg, "output1")

        timestamp = datetime(2018, 7, 8)
        with open("/data/stomach.csv") as csvf:
            csvReader = csv.DictReader(csvf)
            for rows in csvReader:
                date = datetime.strptime(rows["Timestamp"], "%Y-%m-%d %H:%M:%S").replace(minute=0, second=0)
                if date != timestamp:
                    time.sleep(10)
                    timestamp = date
                    print(date)
                await asyncio.gather(*[send_async_message(rows)])

        print("finished...")

        while True:
            pass

        await module_client.disconnect()

    except Exception as e:
        print ( "Unexpected error %s " % e )
        raise

if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    loop.run_until_complete(main())
    loop.close()

    # If using Python 3.7 or above, you can use following code instead:
    # asyncio.run(main())