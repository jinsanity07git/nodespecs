import socket
import getpass


def get_current_user():
    username = getpass.getuser()
    return username

def get_hostname():
    hostname = socket.gethostname()
    return hostname

def whoish(width = 20):
    print("Hostname:".ljust(width), get_hostname())
    print("Current User:".ljust(width), get_current_user())

if __name__ == "__main__":
    whoish()