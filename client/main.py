from client import MyClient

client = MyClient()  # Initialize our client


# Function to set up the socket and connect to the server
def start_client():
    # Wait until the client is stopped
    while not client.exit:
        pass


if __name__ == "__main__":
    start_client()
