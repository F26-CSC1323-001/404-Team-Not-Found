
import socket

PI_IP = "192.168.1.202"
PORT = 5050


def send_status(message):
    try:
        with socket.create_connection((PI_IP, PORT), timeout=5) as client:
            client.sendall(message.encode("utf-8"))
            response = client.recv(1024).decode("utf-8")
            print("Raspberry Pi:", response)

    except OSError as error:
        print("Connection failed:", error)


if __name__ == "__main__":
    while True:
        print("\nSMART ATTENDANCE LED TEST")
        print("1. Successful attendance")
        print("2. Failed verification")
        print("3. Already marked")
        print("4. Test connection")
        print("5. Exit")

        choice = input("Choose an option: ")

        messages = {
            "1": "SUCCESS",
            "2": "FAILED",
            "3": "ALREADY_MARKED",
            "4": "HELLO"
        }

        if choice == "5":
            break

        if choice in messages:
            send_status(messages[choice])
        else:
            print("Invalid option")
