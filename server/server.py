import json
import pickle
import threading

from socket import *

import motor.stepper_motor as sp


# This only works with the gpio version of the stepper_motor.py
class MyServer:
    def __init__(self):
        self.__ECHO_PORT = 50000  # Port for the server
        self.__BUFSIZE = 1024  # Set maximum bufsize

        self.name = f"{gethostname()}:{self.__ECHO_PORT}"

        self._motor = sp.StepperMotor()  # Initialize stepper motor object

        self.data_recv = None  # Storage for received messages
        self.data_send = None  # Storage for sent messages

        self.socket_connection = socket(AF_INET, SOCK_STREAM)  # Create IpV4-TCP/IP-socket
        self.socket_connection.setsockopt(SOL_SOCKET, SO_REUSEADDR, 1)  # Make IP reusable
        self.socket_connection.bind(('', self.__ECHO_PORT))  # Bind IP to socket
        self.socket_connection.listen(1)  # Listen for clients -> execute the following code after connection

        print("Server is running.")
        print(f"Server-Device: {gethostname()}")
        print(f"Server-IP Address: {gethostbyname(gethostname())}")

        # Wait until the client accepted the connection with the server
        # The variable self.conn stores every available information about the client
        self.conn, (self.remotehost, self.remoteport) = self.socket_connection.accept()
        print(f"Connected with '{self.remotehost}:{self.remoteport}'.")  # Print data about client

        self.exit = False  # Initiate boolean to end it all
        self.quit = False  # Initiate boolean to stop threads

        self.thread_recv = threading.Thread(target=self.worker_recv)  # Setup thread for receiving messages
        self.thread_recv.start()  # Start thread to receive messages

        self.lock = threading.Lock()

    # Function to receive messages
    def worker_recv(self):
        motor_action = 0

        while not self.quit:  # While self.exit is false
            try:
                self.data_recv = self.conn.recv(self.__BUFSIZE)  # Receive data from the client with certain bufsize
            except Exception as e:  # Catch error and print
                print(f"Error in receiving data: {e}")
                break
            # Receive data from the client with certain bufsize
            with self.lock:  # Aquire lock so nothing can execute while the worker is running
                if self.data_recv:  # If server receives data from the client
                    json_object = self.decode_json(self.data_recv)

                    temperature = json_object["Temperature"]
                    degrees = json_object["Degrees"]

                    print(f"Received data: {temperature}°C, {degrees}°")

                    if degrees < 0:
                        degrees *= -1
                        threading.Thread(target=self._motor.do_counterclockwise_degrees(degrees)).start()
                    else:
                        threading.Thread(target=self._motor.do_clockwise_degrees(degrees)).start()

    # Function to decode json
    def decode_json(self, message):
        json_string = pickle.loads(message)
        json_object = json.loads(json_string)

        return json_object
