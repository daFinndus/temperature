from server import MyServer

server = MyServer()  # Initialize our server


# Function to set up the socket and start our server
def start_server():
    # Wait until the server is stopped
    while not server.exit:
        pass


if __name__ == "__main__":
    start_server()  # Start our server
