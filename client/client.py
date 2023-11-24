import json
import pickle
import threading
import time

from socket import *
from threading import Thread
from temperature_sensor.temp_sens import TempSensor


# This only works with the gpio version of the stepper_motor.py
class MyClient:
    def __init__(self):
        self.__SERVER_PORT = 50000  # Port for the server
        self.__BUFSIZE = 1024  # Set maximum bufsize

        self.gain = 1
        self.samples_per_second = 64
        self.temperature_sensor = TempSensor(self.gain, self.samples_per_second)

        self.__TEMP_MIN = 25  # Minimum temperature
        self.__TEMP_MAX = 30  # Maximum temperature

        self.temp = self.temperature_sensor.measure_temp()  # Store the last temperature value
        print(f"Init temperature: {self.temp}°C")
        self.temp_diff = 0  # Store the last temperature difference value

        self.degrees = 90 if self.temp >= 30 else 0  # Store the last degrees value
        print(f"Init degrees: {self.degrees}°")
        self.degrees_diff = 90 if self.temp >= 30 else 0  # Store the last degree difference value
        print(f"Init degrees_diff: {self.degrees_diff}°")

        self.host = input("\nEnter Server-IP Address: ").replace(" ", "")  # Set IP of host
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

    # Function for receiving the temperature and degrees from our sensor
    def get_temp(self):
        temp_last = self.temp  # Store the last temperature value
        temp_new = self.temperature_sensor.measure_temp()  # Get the current temperature

        if self.__TEMP_MIN <= temp_new <= self.__TEMP_MAX:
            temp_last = max(self.__TEMP_MIN, min(temp_last, self.__TEMP_MAX))
            temp_new = max(self.__TEMP_MIN, min(temp_new, self.__TEMP_MAX))

            self.temp_diff = temp_new - temp_last  # Calculate the difference between our two temperatures
        else:
            self.temp_diff = 0

        self.temp = temp_new  # Set the current temperature as the last temperature
        self.temp_diff = round(self.temp_diff, 2)  # Round the temperature difference to 2 decimal places

        print(f"Current temperature: {self.temp}°C, Temperature difference: {self.temp_diff}°C")

        return self.temp  # Return the current temperature

    # Function to translate our temperature difference into degrees
    def get_degrees(self):
        degrees = round(self.temp_diff * 18, 1)  # Calculate the degrees from the temperature difference
        degrees_diff = self.degrees_diff  # Store the last degree difference

        self.degrees_diff += degrees  # Set the current degree difference as the last degree difference
        self.degrees = degrees  # Set the current degrees as the last degrees

        # Check if the degree difference is less than 0 or the temperature is the minimum temperature
        if self.degrees_diff < 0 or self.temp <= self.__TEMP_MIN:
            self.degrees = 0 - degrees_diff  # Moving exactly to 0°
            self.degrees_diff = 0  # Set the degree difference to 0
        # Check if the degree difference is greater than 90 or the temperature is the maximum temperature
        elif self.degrees_diff > 90 or self.temp >= self.__TEMP_MAX:
            self.degrees = 90 - degrees_diff  # Moving to 90°
            self.degrees_diff = 90  # Set the degree difference to 90

        degrees = self.degrees  # Store the degrees
        degrees_diff = self.degrees_diff  # Store the degree difference

        print(f"Moving degrees: {self.degrees}°, Total degrees: {self.degrees_diff}°")

        return degrees, degrees_diff  # Return the degrees and the degree difference

    # Function to send messages
    def worker_send(self):
        while not self.quit:
            try:
                temp_data = self.get_temp()  # Get the current temperature
                degrees_data, degrees_diff_data = self.get_degrees()  # Degrees the motor should turn

                json_string = self.encode_json(temp_data, degrees_data, degrees_diff_data)  # Store into json object
                byte_message = self.encode_pickle(json_string)  # Translate our json object into bytes

                self.data_send = byte_message  # Store the bytes into the data_send variable

                # Send the server the data_send string
                self.socket_connection.send(self.data_send)

                # Sleep for three seconds
                time.sleep(3)
            except Exception as e:  # Catch error and print
                print(f"Error occurred in sending message: {e}")
                threading.Thread(target=self.shutdown).start()
        print("Stopped thread because self.quit is true.")

    # Function to turn a message into json
    @staticmethod
    def encode_json(temp, degrees, degrees_diff):
        json_object = {"temperature": temp, "degrees": degrees, "degrees_diff": degrees_diff}
        # Also give frequency (speed) and degrees in the object
        json_string = json.dumps(json_object)

        return json_string

    # Function to turn a message into pickle
    @staticmethod
    def encode_pickle(json_string):
        byte_message = pickle.dumps(json_string)
        return byte_message

    # Function to shut down the client
    def shutdown(self):
        self.quit = True  # Stop the thread
        self.exit = True  # Stop the whole application
        print("Shutting down client..")
        time.sleep(1)
        self.thread_send.join()  # Wait until the thread is stopped
        print("Stopping thread..")
        time.sleep(1)
        self.socket_connection.close()  # Close the socket connection
        print("Connection closed.")
        time.sleep(1)
        exit()
