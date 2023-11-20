import json
import pickle
import threading
import time
from socket import *
from threading import Thread

from temperature_sensor.temp_sens import TempSensor

# Dictionary of help commands
_help_dict = {
    "help": "Display the help menu.",
    "set [number]": "Set the delay after each step in Hz.",
    "cw-step [number]": "Move clockwise in steps.",
    "ccw-step [number]": "Move counterclockwise in steps.",
    "cw-degrees [number]": "Move the motor clockwise by degrees.",
    "ccw-degrees [number]": "Move the motor counterclockwise by degrees.",
    "disconnect": "Disconnect from the server.",
    "shutdown": "Shutdown the application, client and server."
}


# This only works with the gpio version of the stepper_motor.py
class MyClient:
    def __init__(self):
        self.__SERVER_PORT = 50000  # Port for the server
        self.__BUFSIZE = 1024  # Set maximum bufsize

        self.gain = 1
        self.samples_per_second = 64
        self.temperature_sensor = TempSensor(self.gain, self.samples_per_second)

        self.host = input("Enter Server-IP Address: ").replace(" ", "")  # Set IP of host
        self.name = f"{gethostname()}:{self.__SERVER_PORT}"

        self.data_recv = None  # Storage for received messages
        self.data_send = None  # Storage for sent messages

        self.socket_connection = socket(AF_INET, SOCK_STREAM)  # Create IpV4-TCP/IP-socket
        self.socket_connection.connect((self.host, self.__SERVER_PORT))  # Connect to the server via IP and port

        print(f"Connected to Server: '{self.host}'.")

        self.exit = False  # Initiate boolean to end it all
        self.quit = False  # Initiate boolean to stop threads

        self.editJSON = False

        self.thread_send = Thread(target=self.worker_send)  # Setup thread for sending messages
        self.thread_send.start()  # Start thread to send messages

        self.lock = threading.Lock()  # Lock for the shutdown function

    # Function to send messages
    def worker_send(self):
        while not self.quit:
            try:
                temp_raw = self.temperature_sensor.measure_temp()
                temp_json = self.encode_json(temp_raw)
                temp_pickle = self.encode_pickle(temp_json)

                self.data_send = temp_pickle

                # Send the server the data_send string
                self.socket_connection.send(self.data_send)

                # Sleep for a second
                time.sleep(1)
            except Exception as e:  # Catch error and print
                print(f"Error occurred in sending message: {e}")
        print("Stopped thread because self.quit is true.")

    # Function to turn a message into json
    def encode_json(self, temp_raw):
        json_object = {}
        # Also give frequency (speed) and degrees in the object
        json_object["Temperature"] = temp_raw
        json_string = json.dumps(json_object)
        return json_string

    # Function to turn a message into pickle
    @staticmethod
    def encode_pickle(json_string):
        byte_message = pickle.dumps(json_string)
        return byte_message

    # Function to stop the connection - Doesn't close the application
    def stop_connection(self):
        self.quit = True  # Stop the while loop in worker_send
        time.sleep(1)
        self.thread_send.join()  # Stop thread for sending messages
        print("Stopped thread for sending messages.")
        time.sleep(1)
        self.socket_connection.close()  # Close socket
        print(f"Stopped connection for: {self.name}")
        time.sleep(1)
        print("Closing the application...")
        time.sleep(1)
        self.exit = True  # Stop the whole application
        exit(0)

    # Function to shut down the application
    def shutdown(self):
        with self.lock:
            print("Shutting down...")
            self.stop_connection()
