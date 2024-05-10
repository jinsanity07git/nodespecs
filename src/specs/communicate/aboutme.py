import socket
import getpass


def get_current_user():
    username = getpass.getuser()
    return username

def get_hostname():
    hostname = socket.gethostname()
    return hostname

def whoish(width = 20,slient=False):
    aboutme = (get_hostname(),
               get_current_user() )
    if not slient:
        print("Hostname:".ljust(width),    aboutme[0] )
        print("Current User:".ljust(width),aboutme[1] )
    return aboutme


def string_to_ascii_list(s):
    return [ord(char) for char in s]

def derive_uid():
    aboutme = whoish(slient=True)
    sshlogin =  f"{aboutme[1]}@{aboutme[0]}"

    ascii_values = string_to_ascii_list(sshlogin)
    uid = f"{sum(ascii_values):05}"
    return sshlogin, uid[:5]

if __name__ == "__main__":
    # whoish()
    print (derive_uid())