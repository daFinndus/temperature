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
        while not self.quit:  # While self.exit is false
            try:
                self.data_recv = self.conn.recv(self.__BUFSIZE)  # Receive data from the client with certain bufsize
            except Exception as e:  # Catch error and print
                print(f"Error in receiving message: {e}")
                break
            # Receive data from the client with certain bufsize
            with self.lock:  # Aquire lock so nothing can execute while the worker is running
                if self.data_recv:  # If server receives data from the client
                    print(f"Received message: {self.decode_json(self.data_recv)}")
        print("Stopped thread because self.quit is true.")

    # Function to decode json
    def decode_json(self, message):
        # Dictionary with all available functions
        functions = {
            "help": self.return_help,
            "set": self._motor.set_stepper_delay,
            "cw-step": self._motor.do_clockwise_step,
            "ccw-step": self._motor.do_counterclockwise_step,
            "cw-degrees": self._motor.do_clockwise_degrees,
            "ccw-degrees": self._motor.do_counterclockwise_degrees,
            "disconnect": self.reset_connection,
            "shutdown": self.shutdown,
        }

        json_string = pickle.loads(message)
        json_object = json.loads(json_string)

        # Iterate through the json object
        for function, amount in json_object.items():
            # Check if the received message is a registered function
            if function == "disconnect":
                threading.Thread(target=self.reset_connection).start()
            elif function == "shutdown":
                threading.Thread(target=self.shutdown).start()
            elif function in functions:
                functions[function](int(amount))
            else:
                print("Couldn't find function in dictionary.")

        return json_object

    # Function to print the help statement
    @staticmethod
    def return_help():
        print("The client has requested the help menu.")

    # Reset the current connection and listen for clients again - Doesn't listen for clients again
    def reset_connection(self):
        print(f"Client {self.remotehost}:{self.remoteport} has disconnected.")
        self.socket_connection.close()  # Socket schließen
        print(f"Closed socket for: {self.name}")
        time.sleep(1)
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
        self.thread_recv = threading.Thread(target=self.worker_recv)
        self.thread_recv.start()

    # Function to shut down the application
    def shutdown(self):
        try:
            self.quit = True  # Stop the while loop in worker_recv
            self.thread_recv.join()
            print("Stopped thread for receiving new messages.")
            self._motor.clean_up_gpio()
            print("Disabled stepper motor and cleaned up all pins.")
            time.sleep(1)
            self.socket_connection.close()  # Close socket
            print(f"Stopped connection for: {self.name}")
            self.exit = True  # Stop the whole application
        except KeyboardInterrupt:
            self._motor.clean_up_gpio()
            exit(1)
        finally:
            print("Shutting down...")
            time.sleep(3)
            exit(0)
