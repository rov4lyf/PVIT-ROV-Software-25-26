import pygame
import time


pygame.init()
pygame.joystick.init()


joystick = pygame.joystick.Joystick(0)
joystick.init()
print(f"Using controller: {joystick.get_name()}\n")


try:
    while True:
        pygame.event.pump()


        left_x = round(joystick.get_axis(0), 2)
        left_y = round(joystick.get_axis(1), 2)
        right_x = round(joystick.get_axis(3), 2)
        right_y = round(joystick.get_axis(4), 2)


        left_trigger = round(joystick.get_axis(2), 2) if joystick.get_numaxes() > 2 else 0
        right_trigger = round(joystick.get_axis(5), 2) if joystick.get_numaxes() > 5 else 0


        a_button = joystick.get_button(0)
        b_button = joystick.get_button(1)
        x_button = joystick.get_button(2)
        y_button = joystick.get_button(3)


        print(
            f"LX: {left_x:>5} | LY: {left_y:>5} | RX: {right_x:>5} | RY: {right_y:>5} | "
            f"LT: {left_trigger:>5} | RT: {right_trigger:>5} | "
            f"A:{a_button} B:{b_button} X:{x_button} Y:{y_button}"
        )


        time.sleep(0.1)


except KeyboardInterrupt:
    print("\nExiting...")
finally:
    pygame.quit()

