import time

from client import MyClient


# Function to set up the socket and connect to the server
def start_client():
    client = MyClient()

    # Wait until the client is stopped
    while not client.exit:
        pass


if __name__ == "__main__":
    try:
        start_client()
    except KeyboardInterrupt as e:
        print("Application will be closed..")
        time.sleep(1)
        exit()
