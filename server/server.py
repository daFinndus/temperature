import json
import pickle
import time

from threading import Thread
from socket import *

import motor.stepper_motor as sp


# This only works with the gpio version of the stepper_motor.py
class MyServer:
    def __init__(self):

        self.__ECHO_PORT = 50000  # Port for the server
        self.__BUFSIZE = 1024  # Set maximum bufsize

        self.name = f"{gethostname()}:{self.__ECHO_PORT}"  # Name of the server

        self._motor = sp.StepperMotor()  # Initialize stepper motor object
        self._motor_power = None  # Boolean to check if the motor is on or off

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

        self.thread_recv = Thread(target=self.worker_recv)  # Setup thread for receiving messages
        self.thread_func = Thread(target=self.input_function)  # Setup thread for receiving messages

        self.thread_recv.start()  # Start thread to receive messages
        self.thread_func.start()  # Start thread to input functions

        self.temp = 0
        self.degrees = 0
        self.degrees_diff = 0

    # Function to receive messages
    def worker_recv(self):
        motor_thread = None  # Initialize motor thread

        while not self.quit:  # While self.exit is false
            self.data_recv = self.conn.recv(self.__BUFSIZE)  # Receive data from the client with certain bufsize

            # Receive data from the client with certain bufsize
            if self.data_recv:  # If server receives data from the client
                json_object = self.decode_json(self.data_recv)

                temperature = json_object["temperature"]  # Get the temperature from the json object
                self.temp = temperature
                degrees = json_object["degrees"]  # Get the degrees from the json object
                self.degrees = degrees
                degrees_diff = json_object["degrees_diff"]  # Get the degrees difference from the json object
                self.degrees_diff = degrees_diff

                # Checks if the temperature is below 25°C or above 30°C and the motor doesn't need to move anymore
                if 25 <= temperature <= 30 and 90 >= degrees_diff >= 0 != degrees:
                    self._motor_power = True  # Set our boolean to true
                    self._motor = sp.StepperMotor()  # Turn on the motor
                else:
                    if motor_thread is not None:  # Check if the variable is not None
                        if not motor_thread.is_alive():  # Check if the thread is currently working
                            self._motor_power = False  # Set our boolean to false
                            self._motor.clean_up_gpio()  # Turn off the motor

                # Start a thread which moves the motor by the given degrees
                if self._motor_power:  # Check if the power is on to prevent errors
                    if degrees < 0:  # Checks if the degrees are negative
                        degrees *= -1  # Make the degrees positive
                        motor_thread = Thread(target=self._motor.do_counterclockwise_degrees(degrees))
                        motor_thread.start()
                    elif degrees > 0:  # Checks if the degrees are positive
                        motor_thread = Thread(target=self._motor.do_clockwise_degrees(degrees))
                        motor_thread.start()

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
            "reset": lambda: Thread(target=self.reset_connection).start(),
            "shutdown": lambda: Thread(target=self.shutdown).start(),
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
            "reset": "Reset the current connection and listen for clients again.",
            "shutdown": "Shutdown the server.",
        }

        for help_function, description in _help_dict.items():
            print(f"{help_function}: {description}")

    def return_info(self):
        print(f"Temperature: {self.temp}°C, Total-Degrees: {self.degrees}°")

    # Reset the current connection and listen for clients again
    def reset_connection(self):
        print(f"Client {self.remotehost}:{self.remoteport} has disconnected.")
        self.socket_connection.close()  # Socket schließen
        print(f"Closed socket for: {self.name}")
        print(f"Sleeping for 5 seconds...")
        time.sleep(5)
        self.quit = True  # Stop everything that depends on exit
        self.thread_recv.join()  # Thread für den Empfang beenden
        print(f"Stopped thread for receiving new messages.")

        # Erneut auf Verbindungen warten
        print("Going to setup the socket again...")
        time.sleep(1)
        self.socket_connection = socket(AF_INET, SOCK_STREAM)  # Create IpV4-TCP/IP-socket
        self.socket_connection.setsockopt(SOL_SOCKET, SO_REUSEADDR, 1)  # Make IP reusable
        self.socket_connection.bind(('', self.__ECHO_PORT))  # Bind IP to socket
        self.socket_connection.listen(1)  # Warten auf neue Clients

        print("Waiting for a new client...")

        # Warten auf neue Verbindung
        self.conn, (self.remotehost, self.remoteport) = self.socket_connection.accept()
        print(f"Connected with '{self.remotehost}:{self.remoteport}'.")

        # Starten des Empfangsthreads für den neuen Client
        self.quit = False

        self.thread_recv = Thread(target=self.worker_recv)  # Setup thread for receiving messages
        self.thread_func = Thread(target=self.input_function)  # Setup thread for receiving messages

        self.thread_recv.start()  # Start thread to receive messages
        self.thread_func.start()  # Start thread to input functions

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
