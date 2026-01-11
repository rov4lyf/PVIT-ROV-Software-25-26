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


        left_h = round(joystick.get_axis(0), 2)
        left_v = -1 * round(joystick.get_axis(1), 2)
        right_v = -1 * round(joystick.get_axis(3), 2)
        D = round(joystick.get_axis(4), 2)


        right_h = round(joystick.get_axis(2), 2) if joystick.get_numaxes() > 2 else 0
        right_trigger = round(joystick.get_axis(5), 2) if joystick.get_numaxes() > 5 else 0

        left_trigger = round(joystick.get_axis(5), 2) if joystick.get_numaxes() > 5 else 0

        Left_button = joystick.get_button(4)
        Right_button = joystick.get_button(5)
        a_button = joystick.get_button(0)
        b_button = joystick.get_button(1)
        x_button = joystick.get_button(2)
        y_button = joystick.get_button(3)


        print(
            f"LH: {left_h:>5} | LV: {left_v:>5} | RH: {right_h:>5} | RV: {right_v:>5} | "
            f"LB: {Left_button} | RB: {Right_button} | " 
            f"A:{a_button} B:{b_button} X:{x_button} Y:{y_button}"
            f"LT: {left_trigger} "
        )


        time.sleep(0.1)


except KeyboardInterrupt:
    print("\nExiting...")
finally:
    pygame.quit()

