import pygame
import socket
import json
import time

# ==== CONFIGURATION ====
PI_IP = "192.168.2.2"  # <-- replace with your Raspberry Pi’s IP
PORT = 60000            # arbitrary port (can be any unused number)
# =======================

# Initialize pygame and controller
pygame.init()
pygame.joystick.init()
joystick = pygame.joystick.Joystick(0)
joystick.init()
print(f"✅ Sending controller data to {PI_IP}:{PORT}")

# Setup UDP socket
sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
sock.connect((PI_IP, PORT))

try:
    while True:
        pygame.event.pump()

        # Gather values
        data = {
            "lx": round(joystick.get_axis(0), 2),
            "ly": round(joystick.get_axis(1), 2),
            "rx": round(joystick.get_axis(3), 2),
            "ry": round(joystick.get_axis(4), 2),
            "a": joystick.get_button(0),
            "b": joystick.get_button(1),
            "x": joystick.get_button(2),
            "y": joystick.get_button(3)
        }

        # Send JSON-encoded data
        message = json.dumps(data).encode()
        sock.sendall(message)

        print(f"Sent: {data}")
        time.sleep(0.05)

except KeyboardInterrupt:
    print("\nStopped.")
finally:
    sock.close()
    pygame.quit()