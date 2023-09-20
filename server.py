from threading import Thread
import pickle
import socket

name = socket.gethostname()
ip = socket.gethostbyname(name)
port = 8000
address = ip, port

server_socket = socket.socket()

max_size = 16
max_data_size = 2 ** max_size

help_file = [
    r"\clients or",
    r"\connections: Get a list of clients",
    r"\admin (Just clients): Check if you are an admin",
    r"\public <message>: Send a message to everyone",
    r"\to <to> <message> or",
    r"\private <to> <message>: Send a message to a specific person (if server allows private messages)",
    r"\quit or",
    r"\exit: Leave server"
]

admin_help_file = [
    r"\is_admin <user>: Check if an user is an admin",
    r"\make_admin <user>: Make an user an admin",
    r"\make_member <user>: Make an user a member",
    r"\allow_private: Allow to send private messages",
    r"\forbid_private: Forbid to send private messages",
    r"\leave <user>: Make an user leave this server"
]


class Connection:
    def __init__(self, user_name: str, socket_: socket.socket, addr: tuple, admin: bool):
        self.user_name = user_name

        self.socket = socket_
        self.addr = addr

        data = pickle.dumps(max_size)
        self.socket.send(data)

        self.admin = admin

        self.recv_thread = Thread(target=self.get)
        self.recv_thread.start()

    def __repr__(self):
        return "Connection: " + str(self.addr)

    def log(self, message):
        try:
            data = pickle.dumps(message)
            self.socket.send(data)

        except ConnectionResetError:
            print("Could not log to", self.user_name)

    def get(self):
        global allow_privates

        while True:
            try:
                data = self.socket.recv(max_data_size)
                text_ = pickle.loads(data)

                if text_[0] == "\\":
                    command_ = text_[1:].split(" ")
                    func_ = command_[0]
                    pars_ = command_[1:]

                    if func_ in ("clients", "connections"):
                        self.log(f":: Users ({len(connections)}) ::")

                        for connection_ in connections:
                            result = connection_.user_name

                            if self.admin:
                                if connection_.admin:
                                    result += " (Admin)"

                                result += " " + str(connection_.addr)

                            self.log(result)

                    elif func_ == "public":
                        log(merge(pars_))

                    elif func_ in ("to", "private"):
                        if allow_privates or self.admin:
                            to_ = pars_[0]
                            text_ = merge(pars_[1:])

                            found_ = find_connection(to_)

                            if found_ is None:
                                self.log("[ERROR] User " + to_ + " not found")

                            else:
                                found_.log(f"[Private:System] " + text_)

                        else:
                            self.log("[System] Private messages are not allowed")

                    elif func_ == "is_admin":
                        if self.admin:
                            to_ = pars_[0]

                            found_ = find_connection(to_)

                            if found is None:
                                self.log("[ERROR] User " + to_ + " not found")

                            else:
                                self.log(found_.admin)

                        else:
                            self.log("[System] You don't have permissions to run this command")

                    elif func_ == "make_admin":
                        if self.admin:
                            to_ = pars[0]

                            found_ = find_connection(to_)

                            if found_ is None:
                                self.log("[ERROR] User " + to_ + " not found")

                            else:
                                found_.admin = True
                                found_.log("[System] Admin " + self + " made you an admin")

                        else:
                            self.log("[System] You don't have permissions to run this command")

                    elif func_ == "admin":
                        if self.admin:
                            self.log("[System] You are an admin")

                        else:
                            self.log("[System] You are not an admin")

                    elif func_ == "allow_private":
                        if self.admin:
                            allow_privates = True

                        else:
                            self.log("[System] You don't have permissions to run this command")

                    elif func_ == "forbid_private":
                        if self.admin:
                            allow_privates = False

                        else:
                            self.log("[System] You don't have permissions to run this command")

                    elif func_ == "leave":
                        if self.admin:
                            user_ = pars[0]

                            found_ = find_connection(user_)

                            if found_ is None:
                                self.log("[System] User not found")

                            else:
                                found_.log("[System] An admin made you leave")
                                connections.remove(found)
                                quit(found_.recv_thread)

                        else:
                            self.log("[System] You don't have permissions to run this command")

                    elif func_ in ("?", "help"):
                        self.log_list(help_file + (admin_help_file if self.admin else []))

                    else:
                        self.log("Unknown command: " + func_)

                else:
                    public_message(self.user_name, text_)

            except ConnectionResetError:
                try:
                    connections.remove(self)
                    log("[System] " + self.user_name + " leaved")
                    quit(self.recv_thread)

                except ValueError as er:
                    print("Could not connect", self.user_name, "\n", er)

    def log_list(self, messages):
        for message in messages:
            self.log(message)


def public_message(user_name, message):
    log(f"[{user_name}] " + message)


def merge(iterable):
    result = iterable[0]
    for item in iterable[1:]:
        result += " " + item
    return result


def accept_connections():
    server_socket.listen()
    print("Waiting users")
    while True:
        print("Waiting connection")
        connection_ = server_socket.accept()
        client_socket, client_addr = connection_
        print("Got connection:", *client_addr)

        try:
            user_name_data = client_socket.recv(256)
            user_name = pickle.loads(user_name_data)
            ok = find_connection(user_name)

            while True:
                if ok is None:
                    client_socket.send(b"1")
                    connections.append(Connection(user_name, client_socket, client_addr, False))
                    log("[Server] " + user_name + " connected")
                    break

                else:
                    client_socket.send(b"2")

        except Exception as ex_:
            print("ERROR while connecting client:", ex_)

            client_socket.send(b"0")


def safe_quit():
    print("Server closed")
    server_socket.close()
    quit()


def log_clients(message):
    for connection_ in connections:
        connection_.log(message)


def log(message):
    print(message)
    log_clients(message)


def find_connection(user_name):
    found_ = None

    for connection_ in connections:
        if connection_.user_name == user_name:
            found_ = connection_
            break

    return found_


try:
    server_socket.bind(address)
    print("Server address:", *address)

    connections = []

    accepting = Thread(target=accept_connections)
    accepting.start()

    allow_privates = True

    while True:
        command = input().split(" ")

        func = command[0]
        pars = command[1:]

        if func in ("clients", "connections"):
            print(f":: Users ({len(connections)}) ::")
            for connection in connections:
                result = connection.user_name

                if connection.admin:
                    result += " (Admin)"

                result += connection.addr

                print(result)

        elif func == "public":
            log(merge(pars))

        elif func in ("to", "private"):
            to = pars[0]
            text = merge(pars[1:])

            found = find_connection(to)

            if found is None:
                print("User " + to + " not found")

            else:
                found.log(f"[Private:System] " + text)

        elif func == "is_admin":
            to = pars[0]

            found = find_connection(to)

            if found is None:
                print("User " + to + " not found")

            elif found.admin:
                print("User " + to + " is an admin")

            else:
                print("User " + to + " is not an admin")

        elif func == "make_admin":
            to = pars[0]

            found = find_connection(to)

            if found is None:
                print("User " + to + " not found")

            else:
                found.admin = True
                found.log("[System] Server made you an admin")

        elif func == "make_member":
            to = pars[0]

            found = find_connection(to)

            if found is None:
                print("User " + to + " not found")

            else:
                found.admin = False
                found.log("[System] Server made you a member")

        elif func == "allow_private":
            allow_privates = True

        elif func == "forbid_private":
            allow_privates = False

        elif func in ("?", "help"):
            print("No need to use \\ on server")

            for message in help_file + admin_help_file:
                print(message)

        elif func == "leave":
            user = pars[0]

            found = find_connection(user)

            if found is None:
                print("User not found")

            else:
                found.log("[System] An admin made you leave")
                connections.remove(found)
                quit(found.recv_thread)

        else:
            print("Unknown command: " + func)


except Exception as ex:
    print("ERROR:", ex)
    print("Please try to restart")

finally:
    safe_quit()
