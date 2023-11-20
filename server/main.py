import time

from server import MyServer
from motor.stepper_motor import StepperMotor


# Function to set up the socket and start our server
def start_server():
    server = MyServer()  # Initialize our server

    # Wait until the server is stopped
    while not server.exit:
        pass


if __name__ == "__main__":
    try:
        start_server()  # Start our server
    except KeyboardInterrupt as e:
        print("Application will be closed..")
        StepperMotor().clean_up_gpio()
        time.sleep(1)
        exit()
