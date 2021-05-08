# Copyright (c) Microsoft. All rights reserved.
# Licensed under the MIT license. See LICENSE file in the project root for
# full license information.

import time
import os
import sys
import asyncio
from six.moves import input
import threading
from datetime import datetime
import json
from azure.iot.device.aio import IoTHubModuleClient

time_buffer = {}
data_buffer = {}

async def main():
    try:
        if not sys.version >= "3.5.3":
            raise Exception( "The sample requires python 3.5.3+. Current version of Python: %s" % sys.version )
        print ( "IoT Hub Client for Python" )

        # The client object is used to interact with your Azure IoT hub.
        module_client = IoTHubModuleClient.create_from_edge_environment()

        # connect the client.
        await module_client.connect()

        # define behavior for receiving an input message on input1
        async def input1_listener(module_client):
            global time_buffer
            global data_buffer
            while True:
                input_message = await module_client.receive_message_on_input("input1")  # blocking call
                data = json.loads(input_message.data.decode('utf-8'))
                animal_id = data["Animal_ID"]
                timestamp = data["Timestamp"]
                date = datetime.strptime(timestamp, "%Y-%m-%d %H:%M:%S").replace(minute=0, second=0)
                if animal_id not in time_buffer:
                    time_buffer[animal_id] = date
                    data_buffer[animal_id] = {"temp_without_drink_cycles": [], "animal_activity": []}
                    data_buffer[animal_id]["temp_without_drink_cycles"].append([timestamp, data["temp_without_drink_cycles"]])
                    data_buffer[animal_id]["animal_activity"].append([timestamp, data["animal_activity"]])
                else:
                    if time_buffer[animal_id] != date:
                        output_message = {}
                        output_message["Animal_ID"] = animal_id
                        output_message["Timestamp"] = str(time_buffer[animal_id].date())
                        output_message["Hours"] = str(time_buffer[animal_id])
                        output_message["Temperature"] = data_buffer[animal_id]["temp_without_drink_cycles"]
                        output_message["Stomach_Activity"] = data_buffer[animal_id]["animal_activity"]
                        output_message = json.dumps(output_message)
                        print(date)
                        await module_client.send_message_to_output(output_message, "output1")
                        time_buffer[animal_id] = date
                        data_buffer[animal_id] = {"temp_without_drink_cycles": [], "animal_activity": []}
                    data_buffer[animal_id]["temp_without_drink_cycles"].append([timestamp, data["temp_without_drink_cycles"]])
                    data_buffer[animal_id]["animal_activity"].append([timestamp, data["animal_activity"]])

        # define behavior for halting the application
        def stdin_listener():
            while True:
                try:
                    selection = input("Press Q to quit\n")
                    if selection == "Q" or selection == "q":
                        print("Quitting...")
                        break
                except:
                    time.sleep(60)

        # Schedule task for C2D Listener
        listeners = asyncio.gather(input1_listener(module_client))

        print ( "The sample is now waiting for messages. ")

        # Run the stdin listener in the event loop
        loop = asyncio.get_event_loop()
        user_finished = loop.run_in_executor(None, stdin_listener)

        # Wait for user to indicate they are done listening for messages
        await user_finished

        # Cancel listening
        listeners.cancel()

        # Finally, disconnect
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