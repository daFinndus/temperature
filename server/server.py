import json
import pickle
import threading
import time

from socket import *

import motor.stepper_motor as sp


# This only works with the gpio version of the stepper_motor.py
class MyServer:
    def __init__(self):

        self.__ECHO_PORT = 50000  # Port for the server
        self.__BUFSIZE = 1024  # Set maximum bufsize

        self.name = f"{gethostname()}:{self.__ECHO_PORT}"  # Name of the server

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
        self.thread_func = threading.Thread(target=self.input_function)  # Setup thread for receiving messages

        self.thread_recv.start()  # Start thread to receive messages
        self.thread_func.start()  # Start thread to input functions

        self.temp = 0
        self.degrees = 0
        self.degrees_diff = 0

    # Function to receive messages
    def worker_recv(self):
        while not self.quit:  # While self.exit is false
            self.data_recv = self.conn.recv(self.__BUFSIZE)  # Receive data from the client with certain bufsize

            # Receive data from the client with certain bufsize
            if self.data_recv:  # If server receives data from the client
                json_object = self.decode_json(self.data_recv)

                temperature = json_object["temperature"]
                self.temp = temperature
                degrees = json_object["degrees"]
                self.degrees = degrees
                degrees_diff = json_object["degrees_diff"]
                self.degrees_diff = degrees_diff

                # Turn off the motor if the temperature is below or equal to 25°C
                if temperature <= 25:
                    self._motor.clean_up_gpio()  # Turn off the motor
                else:
                    self._motor = sp.StepperMotor()  # Turn on the motor

                # Start a thread which moves the motor by the given degrees
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

    # Function to input functions
    def input_function(self):
        time.sleep(1)

        functions = {
            "help": self.return_help,
            "info": self.return_info,
            "shutdown": lambda: threading.Thread(target=self.shutdown).start(),
        }

        while not self.quit:
            try:
                function = input("> ")
                functions.get(function, lambda: print("Invalid command."))()

                if function == "shutdown":
                    self.quit = True
            except Exception as e:
                print(f"Error in function: {e}")

    # Function to print the help statement
    def return_help(self):
        _help_dict = {
            "info": "Return current temperature and the total degrees the motor has turned.",
            "shutdown": "Shutdown the server.",
        }

        for help_function, description in _help_dict.items():
            print(f"{help_function}: {description}")

    def return_info(self):
        print(f"Temperature: {self.temp}°C, Total-Degrees: {self.degrees}°")

    # Function to shut down the server
    def shutdown(self):
        self.quit = True  # Stop the thread
        self.exit = True  # Stop the whole application
        time.sleep(1)
        print("Shutting down server..")
        self._motor.clean_up_gpio()  # Turn off the motor
        self.socket_connection.close()  # Close the socket
        print("Connection closed.")
        try:
            self.thread_recv.join()
            self.thread_func.join()
            print("Stopped thread because self.quit is true.")
            time.sleep(1)
        except Exception as e:
            print(f"Error in stopping thread: {e}")
        finally:
            print("Closing the application...")
            quit(0)
