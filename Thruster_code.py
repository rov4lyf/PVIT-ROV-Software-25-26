from pyfirmata2 import ArduinoMega
import pygame
import time

board = ArduinoMega('COM3')
print("0")
T1 = board.get_pin('d:2:s')
print("1")
T2 = board.get_pin('d:4:s')
print("2")
T3 = board.get_pin('d:6:s')
print("3")
T4 = board.get_pin('d:8:s')
print("4")
T5 = board.get_pin('d:10:s')
print("5")
T6 = board.get_pin('d:12:s')
print("6")

print("ESC Set Up")
T1.write(91)
T2.write(91)
T3.write(91)
T4.write(91)
T5.write(91)
T6.write(91)
time.sleep(5)


pygame.init()
pygame.joystick.init()
joystick = pygame.joystick.Joystick(0)
joystick.init()
print(f"Using controller: {joystick.get_name()}\n")



def thruster_buttons():
    if x_button == 1:
        T1.write(74)
        print("X pressed")
    if x_button == 0:
        T1.write(91)
        print("X released")
    if y_button == 1:
        T2.write(74)
        print("Y pressed")
    if y_button == 0:
        T2.write(91)
        print("Y released")
    if a_button == 1:
        T3.write(74)
        print("A pressed")
    if a_button == 0:
        T3.write(91)
        print("A released")
    if b_button == 1:
        T4.write(72)
        print("B pressed")
    if b_button == 0:
        T4.write(91)
        print("B released")

    if LB == 1:
        T5.write(73)
        print("LB pressed")
    if LB == 0:
        T5.write(91)
        print("LB released")
    if RB == 1:
        T6.write(72.5)
        print("RB pressed")
    if RB == 0:
        T6.write(91)
        print("RB released")
try:
    while True:
        pygame.event.pump()

        left_x = round(joystick.get_axis(0), 2)
        left_y = round(joystick.get_axis(1), 2)
        right_x = round(joystick.get_axis(3), 2)
        right_y = round(joystick.get_axis(4), 2)

        a_button = joystick.get_button(0)
        b_button = joystick.get_button(1)
        x_button = joystick.get_button(2)
        y_button = joystick.get_button(3)
        
        LB = joystick.get_button(4)
        RB = joystick.get_button(5)
        left_trigger = round(joystick.get_axis(2), 2) if joystick.get_numaxes() > 2 else 0
        right_trigger = round(joystick.get_axis(5), 2) if joystick.get_numaxes() > 5 else 0

        thruster_buttons()
        
        time.sleep(0.1)
except:
    print("Error#1")