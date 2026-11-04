import os
import json
import hmac
import socket
import time
import RPi.GPIO as GPIO

HOST = "0.0.0.0"
PORT = 5050

GREEN_LED = 5
RED_LED = 6

TOKEN = os.environ.get("ATTENDANCE_PI_TOKEN", "")

if not TOKEN:
    raise SystemExit("Set ATTENDANCE_PI_TOKEN first")

GPIO.setmode(GPIO.BCM)
GPIO.setup(GREEN_LED, GPIO.OUT, initial=GPIO.LOW)
GPIO.setup(RED_LED, GPIO.OUT, initial=GPIO.LOW)


def show_status(status):
    GPIO.output(GREEN_LED, GPIO.LOW)
    GPIO.output(RED_LED, GPIO.LOW)

    if status == "SUCCESS":
        print("SUCCESS: Green LED")
        GPIO.output(GREEN_LED, GPIO.HIGH)
        time.sleep(3)

    elif status == "FAILED":
        print("FAILED: Red LED")
        GPIO.output(RED_LED, GPIO.HIGH)
        time.sleep(3)

    elif status == "ALREADY_MARKED":
        print("ALREADY_MARKED: Green blinking")
        for _ in range(2):
            GPIO.output(GREEN_LED, GPIO.HIGH)
            time.sleep(0.5)
            GPIO.output(GREEN_LED, GPIO.LOW)
            time.sleep(0.5)

    GPIO.output(GREEN_LED, GPIO.LOW)
    GPIO.output(RED_LED, GPIO.LOW)


server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

try:
    server.bind((HOST, PORT))
    server.listen(5)
    print("Raspberry Pi server ready on port 5050")

    while True:
        connection, address = server.accept()

        with connection:
            try:
                connection.settimeout(5)
                data = b""

                while b"\n" not in data and len(data) < 1024:
                    chunk = connection.recv(1024 - len(data))
                    if not chunk:
                        break
                    data += chunk

                payload = json.loads(data.split(b"\n", 1)[0])
                received_token = str(payload.get("token", ""))
                status = payload.get("status")

                if not hmac.compare_digest(received_token, TOKEN):
                    connection.sendall(b"DENIED")
                    continue

                if status not in (
                    "SUCCESS", "FAILED", "ALREADY_MARKED", "HELLO"
                ):
                    connection.sendall(b"INVALID")
                    continue

                print("Received:", status, flush=True)
                connection.sendall(b"OK")
                show_status(status)

            except (ValueError, OSError) as error:
                print("Socket error:", error)

except KeyboardInterrupt:
    print("Server stopped")

finally:
    GPIO.output(GREEN_LED, GPIO.LOW)
    GPIO.output(RED_LED, GPIO.LOW)
    GPIO.cleanup()
    server.close()
