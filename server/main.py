from server import MyServer


# Function to set up the socket and start our server
def start_server():
    server = MyServer()  # Initialize our server

    # Wait until the server is stopped
    while not server.exit:
        pass


if __name__ == "__main__":
    start_server()
