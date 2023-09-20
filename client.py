from threading import Thread
import pickle
import socket
import re


def safe_quit():
    print("Leaved chat")
    client_socket.close()
    quit()


def is_addr(addr_):
    addr_.strip()
    return re.match(r"[0-9]*\.[0-9]*\.[0-9]*\.[0-9]* [0-9]*", addr_)


def wait_logs():
    while True:
        try:
            data_ = client_socket.recv(max_data_size)
            text_ = pickle.loads(data_)
            print(text_)

        except ConnectionResetError:
            print("Server closed")
            safe_quit()


client_socket = socket.socket()

while True:
    try:
        addr_str = input("Server address: ")
        while not is_addr(addr_str):
            addr_str = input("Invalid address format (Should be 'ip.ip.ip.ip port')\n")

        addr_str = addr_str.strip()
        while "  " in addr_str:
            addr_str = addr_str.replace("  ", " ")

        addr = addr_str.split(" ")
        addr[1] = int(addr[1])
        addr = tuple(addr)

        valid_username = False

        client_socket.connect(addr)

        while not valid_username:
            user_name = input("Username: ")
            while not (0 < len(user_name) < 32) or user_name.lower() == "server":
                user_name = input("Invalid Username\n")

            user_name_data = pickle.dumps(user_name)
            client_socket.send(user_name_data)
            connected = int(client_socket.recv(256))

            if not connected:
                valid_username = True
                print("ERROR while connecting server. Server refused connection")

            elif connected == 1:
                valid_username = True
                print("Connected to server")

                max_size = pickle.loads(client_socket.recv(4096))
                max_data_size = 2 ** max_size
                print("Max size:", max_data_size)

                waiting = Thread(target=wait_logs)
                waiting.start()

                while True:
                    text = input()
                    if len(text) > 0:
                        data = pickle.dumps(text)

                        if len(data) <= max_data_size:
                            try:
                                client_socket.send(data)
                            except ConnectionResetError:
                                print("Server closed")
                                safe_quit()

                        else:
                            print("Too long")

                    else:
                        print("Please don't spam")

            elif connected == 2:
                print("Invalid username")

    except Exception as ex:
        print("ERROR:", ex)

    finally:
        safe_quit()
