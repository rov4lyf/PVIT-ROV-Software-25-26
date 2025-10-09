#!/usr/bin/env python3
import logging
from threading import Timer
import pyfirmata
import time
from enum import Enum
from modules.ps4.ps4_model import PS4Model

#Defines For Thruster Pins
FL = 12 #escOne = Front Left
FR = 13 #esƒcTwo = Front Right
VL = 11 #escThree = Vertical Left
VR = 8 #escFour = Vertical Right
BL = 6 #escFive = Back Left
BR = 10 #escSix = Back Right
# FL = 47 #Flash Light
# INIT = 49 #relay initialize
CLAW_OPEN_ONE = 25
CLAW_OPEN_TWO = 27
CLAW_CLOSE_ONE = 29
CLAW_CLOSE_TWO = 31
CLAW_ROTATE = 3

#Define Thruster Speeds
class SIGNAL(Enum):
    STOP = 1500 
    FOWARD_MAX = 1900
    REVERSE_MAX = 1100

class MODE(Enum):
    MANUAL = 0
    AUTO_RED_LINE = 1
    AUTO_TRANSECT = 2
    AUTO_HOME = 3


#Signals

SPEED_STOP = 1500.0
SPEED_MAX = 1650
SPEED_MAX_DELTA = 200
SPEED_SLOW = 1550.0
SPEED_MEDIUM = 1600.0

SPEED_UP_DOWN = 0

ON = 1
OFF = 0
RELAY_ON = 1
RELAY_OFF = 0

# direction class
class DIRECTION:
    NONE = 0
    LEFT = 1
    RIGHT = 2
    DOWN = 3
    UP = 4

class AutonomousMovement:
    def __init__(self):
        self["direction"] = DIRECTION.NONE
        self["x"] = 0
        self["y"] = 0
        self["speed"] = 1500
        self["duration"] = 0.0

class Propulsion:
    # create ps4 controller state
    ps4Model = PS4Model()

    throttleValue = 0.2

    variableSpeed = 20

    upValue = 0

    downValue = 0

    # logging reference
    logger: logging.Logger = None

    # create mode
    mode = MODE.MANUAL

    # Keep Track Of Last Button State
    lastControl = "" 
    lastState = -1

    def __new__(cls):
        if not hasattr(cls, "instance"):
            cls.instance = super(Propulsion, cls).__new__(cls)
        return cls.instance
    
    def __init__ (self):
        try:
            # initialize arduino
            board = pyfirmata.ArduinoMega('/dev/ttyACM0')
            # self.logger.info("Communication Successfully started")
            
            # configure arduino pwm pins
            board.servo_config(FL, 1100, 1900) 
            board.servo_config(FR, 1100, 1900)
            board.servo_config(VL, 1100, 1900)
            board.servo_config(VR, 1100, 1900)
            board.servo_config(BL, 1100, 1900)
            board.servo_config(BR, 1100, 1900)
            board.servo_config(CLAW_ROTATE, 1200, 2300, 90)

            # # setup relay init
            # self.relays = board.digital[INIT]
            # self.relays.mode = pyfirmata.DIGITAL

            # # setup EM pin
            # self.flashLight = board.digital[FL]
            # self.flashLight.mode = pyfirmata.DIGITAL

            # setup Claw pins
            self.clawOpenONE = board.digital[CLAW_OPEN_ONE]
            self.clawOpenONE.mode = pyfirmata.DIGITAL

            self.clawOpenTWO = board.digital[CLAW_OPEN_TWO]
            self.clawOpenTWO.mode = pyfirmata.DIGITAL

            self.clawCloseONE = board.digital[CLAW_CLOSE_ONE]
            self.clawCloseONE.mode = pyfirmata.DIGITAL

            self.clawCloseTWO = board.digital[CLAW_CLOSE_TWO]
            self.clawCloseTWO.mode = pyfirmata.DIGITAL

            self.clawRT = board.digital[CLAW_ROTATE]
            self.clawRT.mode = pyfirmata.SERVO

            # setup thruster pins
            self.thrusterFL = board.digital[FL]
            self.thrusterFL.mode = pyfirmata.SERVO
        
            self.thrusterFR = board.digital[FR]
            self.thrusterFR.mode = pyfirmata.SERVO
            
            self.thrusterVL = board.digital[VL]
            self.thrusterVL.mode = pyfirmata.SERVO
            
            self.thrusterVR = board.digital[VR]
            self.thrusterVR.mode = pyfirmata.SERVO
            
            self.thrusterBL = board.digital[BL]
            self.thrusterBL.mode = pyfirmata.SERVO

            self.thrusterBR = board.digital[BR]
            self.thrusterBR.mode = pyfirmata.SERVO

        
            # initialize thrusters with stop
            self.setESC(self.thrusterFL, 1500)
            self.setESC(self.thrusterFR, 1500)
            self.setESC(self.thrusterVL, 1500)
            self.setESC(self.thrusterVR, 1500)
            self.setESC(self.thrusterBL, 1500)
            self.setESC(self.thrusterBR, 1500)
           
            # initialize claw relays to off
            self.CLAW_OFF()

            # initialize flashlight to off
            # self.FL_OFF()

            # initialize default mode
            self.mode = MODE.MANUAL

            self.initialized = True
        except:
            # self.logger.error("Arduino not detected.", exc_info=True)
            self.initialized = True
        
    def setLogger(self, logger: logging.Logger):
        self.logger = logger

    def setESC (self, thruster: pyfirmata.pyfirmata.Pin, val: int):
        try:
            thruster.write(val)
        except:
            # self.logger.error("Error setting thruster.", exc_info=True)
            print("Error setting thruster.")

    def setPT (self, payloadtool: pyfirmata.pyfirmata.Pin, val: int):
        try:
            payloadtool.write(val)
        except:
            self.logger.error("Error setting payload tool.", exc_info=True)

    def clawRotate (self, claw: pyfirmata.pyfirmata.Pin, angle: int):
        try:
            claw.write(angle)
        except:
            self.logger.error("Error rotating claw.", exc_info=True)

    def clear(self):
        self.CLAW_OFF()
        # self.FL_OFF()

    def set_button_status(self, data):
        status = True
        try:
            if data != None:
                # get controller event
                control = data["control"]
                state = data["state"]
                if control == "throttle":
                    self.throttleValue = state
                    self.variableSpeed = self.calcSpeedUpDown(self.throttleValue)
                    if self.upValue == 1:
                        control = "up"
                        state = 1
                        status = self.runManual(control, state)
                    elif self.downValue == 1:
                        control = "down"
                        state = 1
                        status = self.runManual(control, state)
              
                elif control != "up" and control != "down" and (self.upValue == 1 or self.downValue == 1):
                    print("Test: %s" % control)
                    pass 
                
                else: 
                    status = self.runManual(control, state)
                
            self.lastControl = control 
            self.lastState = state
        except:
            status = False
            self.logger.error("Error setting button state.", exc_info=True)

        return status 

    def calcSpeed(self, val):
        speed = SPEED_STOP + (val * SPEED_MAX_DELTA)
        return speed
    
    def calcSpeedMax(self, val):
        speedMax = SPEED_STOP + SPEED_MAX_DELTA
        return speedMax
    
    def calcSpeedUpDown(self, val):
        val += 1
        val /= 2
        percent = ((val*0.8)+0.2)
        return percent * SPEED_MAX_DELTA

    def runManual(self, control, state):
        try:
            
            if control == "throttle": 
                self.calcSpeedUpDown(state)
                # calculate up and down speed
            elif control == "pitch":
                if state > 0:
                    self.moveForward(self.calcSpeed(state)) #again this needs to be edited
                    print(f"Moving fowards at signal: %d" % self.calcSpeed(state))
                elif state < 0:
                    self.moveBackward(self.calcSpeed(-state)) #again this needs to be edited 
                    print("Moving backwards at signal: %d" % self.calcSpeed(state))
                elif state == 0:
                    self.moveBackward(1500)
            # elif control == "roll":
            #     print("Test: in roll");

            #     if state > 0:
            #         print("Test: Strafe right");
            #         self.strafeRight(self.calcSpeed(-1*state))
            #         print("Strafing right at signal: %d" % self.calcSpeed(-1*state))
            #     elif state < 0:
            #         print("Test: Strafe left");
            #         self.strafeLeft(self.calcSpeed(-1*state)) 
            #         print("Strafing left at signal: %d" % self.calcSpeed(-1*state))
            #     elif state == 0:
            #         self.strafeStop(1500)
            #         print("Strafing stopped at signal: %d" % self.calcSpeed(0))
            elif control == "yaw":
                if state > 0:
                    self.rotateRight(self.calcSpeed(state))
                    print("Rotating right at signal: %d" % self.calcSpeed(state))
                elif state < 0:
                    self.rotateLeft(self.calcSpeed(-state))
                    print("Rotating left at signal: %d" % self.calcSpeed(state))
                elif state == 0:
                    self.rotateLeft(1500)
            elif control == "claw_close":
                if state == 1:
                    self.CLAW_OPEN()
                    print("Open Claw")
                elif state == 0:
                    self.CLAW_OFF()
                    print("Claw off")
            elif control == "claw_open":
                if state == 1:
                    self.CLAW_CLOSE()
                    print("Close claw")
                elif state == 0:
                    self.CLAW_OFF()
                    print("Claw off")
            elif control == "hat":
                if state == (0, 1):
                    self.rotateClaw(135)
                    print("Claw rotated at 165 degrees")
                elif state == (-1, 0):
                    self.rotateClaw(115)
                    print("Claw rotated at 130 degrees")
                elif state == (0, -1):
                    self.rotateClaw(75)
                    print("Claw rotated at 100 degrees")
                elif state == (1, 0):
                    self.rotateClaw(155)
                    print("Claw rotated at 65 degrees")
            elif control == "video_off":
                if state == 1:
                    i = 1 #method needs to be added
                    print("Video off")
            elif control == "video_front":
                if state == 1:
                    i = 1 #method needs to be added
                    print("Video front")
            elif control == "video_down":
                if state == 1:
                    i = 1 #method needs to be added
                    print("Video down")
            elif control == "video_dome":
                if state == 1:
                    i = 1 #method needs to be added
                    print("Video dome")
            elif control == "up":
                if state == 1:
                    self.upValue = 1
                    self.moveUp()
                    # self.moveBackward(1350)
                    # print("Moving up at signal: %d" % self.calcSpeed(state))
                elif state == 0:
                    self.upValue = 0
                    self.noMoveUpDown()
                    # self.moveBackward(1500)
            elif control == "down":
                if state == 1:
                    self.downValue = 1
                    self.moveDown()
                    # self.moveBackward(1350)
                    # print("Moving down at signal: %d" % self.calcSpeed(state))
                elif state == 0:
                    self.downValue = 0
                    self.noMoveUpDown()
                    # self.moveBackward(1500)
            elif control == "fl":
                 if state == 1:
                     self.strafeRight(1600)
                     print("Strafing Right")
                 elif state == 0:
                     self.strafeStop(1500)
                     print("No Strafe")
            elif control == "init":
                 if state == 1:
                     self.strafeLeft(1600)
                     print("Strafing Left")
                 elif state == 0:
                     self.strafeStop(1500)
                     print("No Strafe")
            elif control == "rotate_cw":
                 if state == 1:
                    self.rotateClaw(0)
            
                
            # DEADZONE = 0.2
            # model = self.ps4Model

            # # stop everything first
            # self.stop()
           
            # # thruster operations
            # ltUD = model["leftStickUD"]
            # rtUD = model["rightStickUD"]
            # ltLR = model["leftStickLR"]
            # rtLR = model["rightStickLR"]

            # if model["optionsBtnState"] == 1:
            #     print("in stop")
            #     self.stop()
            # elif ltUD < -DEADZONE or ltUD > DEADZONE or rtUD < -DEADZONE or rtUD > DEADZONE:
            #     print("in stick")
            #     if model["leftStickUD"] > 0.15:
            #         val = model["leftStickUD"]
            #         if val > .90:
            #             val = .90
            #         speed = self.calcSpeed(val)
            #         print(f"ltUD: {val}/{speed}")
            #         self.leftFoward(speed)
            #     elif model["leftStickUD"] < -0.15:
            #         val = model["leftStickUD"]
            #         if val < -.90:
            #             val = -.90
            #         speed = self.calcSpeed(val)
            #         print(f"ltUD: {val}/{speed}")
            #         self.leftBackward(speed)

            #     if model["rightStickUD"] > 0.15:
            #         val = model["rightStickUD"]
            #         if val > .90:
            #             val = .90
            #         speed = self.calcSpeed(val)
            #         print(f"rtUD: {val}/{speed}")
            #         self.rightFoward(speed)
            #     elif model["rightStickUD"] < -0.15:
            #         val = model["rightStickUD"]
            #         if val < -.90:
            #             val = -.90
            #         speed = self.calcSpeed(val)
            #         print(f"rtUD: {val}/{speed}")
            #         self.rightBackward(speed)

            #     if model["leftTriggerPos"] > -1:
            #         print("in ltrig")
            #         val = (model["leftTriggerPos"] + 1) / 2
            #         speedMax = self.calcSpeedMax(val)
            #         self.moveDown(speedMax) 
            #     elif model["leftBtn1State"] == 1:
            #         print("in lbtn")
            #         val = model["leftBtn1State"]
            #         speedMax = self.calcSpeedMax(val)
            #         self.moveUp(speedMax) 
                
            #     if model["hatLRState"] == 1:
            #         print("in hat LR")
            #         speed = self.calcSpeed(.90)
            #         self.strafeRight(speed)
            #     elif model["hatLRState"] == -1:
            #         print("in hat -LR")
            #         speed = self.calcSpeed(.90)
            #         self.strafeLeft(speed)
            # elif ltUD >= -DEADZONE and ltUD <= DEADZONE and rtUD >= -DEADZONE and rtUD <= DEADZONE:        
            #     if model["leftTriggerPos"] > -1:
            #         print("in ltrig")
            #         val = (model["leftTriggerPos"] + 1) / 2
            #         speedMax = self.calcSpeedMax(val)
            #         self.moveDown(speedMax) 
            #     elif model["leftBtn1State"] == 1:
            #         print("in lbtn")
            #         val = model["leftBtn1State"]
            #         speedMax = self.calcSpeedMax(val)
            #         self.moveUp(speedMax) 
            #     elif model["hatLRState"] == 1:
            #         print("in hat LR")
            #         speed = self.calcSpeed(.90)
            #         self.strafeRight(speed)
            #     elif model["hatLRState"] == -1:
            #         print("in hat -LR")
            #         speed = self.calcSpeed(.90)
            #         self.strafeLeft(speed)
            #     else:
            #         print(f"stop ltUD: {ltUD} rtUD: {rtUD}")
            #         self.stop()
            # elif model["hatLRState"] == 1:
            #     print("in hat LR")
            #     speed = self.calcSpeed(.90)
            #     self.strafeRight(speed)
            # elif model["hatLRState"] == -1:
            #     print("in hat -LR")
            #     speed = self.calcSpeed(.90)
            #     self.strafeLeft(speed)
            # elif model["leftTriggerPos"] > -1:
            #     print("in ltrig")
            #     val = (model["leftTriggerPos"] + 1) / 2
            #     speedMax = self.calcSpeedMax(val)
            #     self.moveDown(speedMax) 
            # elif model["leftBtn1State"] == 1:
            #     print("in lbtn")
            #     val = model["leftBtn1State"]
            #     speedMax = self.calcSpeedMax(val)
            #     self.moveUp(speedMax) 
            # else:
            #     self.stop()
            
            # # claw rotation operations
            # if model["circleBtnState"] == 1:
            #     print("rotate 120")
            #     self.Rotate120()
            # elif model["squareBtnState"] == 1:
            #     print("rotate 90")
            #     self.Rotate90()
            # elif model["triangleBtnState"] == 1:
            #     print("rotate 65")
            #     self.Rotate65()
            # elif model["crossXBtnState"] == 1:
            #     print("rotate 35")
            #     self.Rotate35()

            # #claw finger operations
            # if model["rightTriggerPos"] > -1:
            #     self.CLAW_CLOSE()
            # elif model["rightBtn1State"] == 1:
            #     self.CLAW_OPEN()
            # elif model["rightBtn1State"] == 0 or model["rightTriggerPos"] == -1:
            #     self.CLAW_OFF()

            # # electro-magnet operations
            # if model["hatUDState"] == 1:
            #     self.EM_ON()
            # else:
            #     self.EM_OFF()

            return True
        except:
            self.logger.exception("Oops ... any magic smoke? LOL")
            return False

    def leftFoward(self, speed):
        # calculate spped for
        speed2 = SPEED_STOP - (speed - SPEED_STOP - 50)
        self.logger.info(f"moving left foward at {speed}")
        self.setESC(self.thrusterFL, speed)
        # self.setESC(self.thrusterBL, speed)

    def leftBackward(self, speed):
        # calculate spped for
        speed2 = SPEED_STOP - (speed - SPEED_STOP - 50)
        self.logger.info(f"moving left backward at {speed}")
        # self.setESC(self.thrusterFL, speed)
        self.setESC(self.thrusterBL, speed)

    def rightFoward(self, speed):
        # calculate spped for
        speed2 = SPEED_STOP - (speed - SPEED_STOP)
        self.logger.info(f"moving right foward at {speed}")
        self.setESC(self.thrusterFR, speed2)
        # self.setESC(self.thrusterBR, speed)

    def rightBackward(self, speed):
        # calculate spped for
        speed2 = SPEED_STOP - (speed - SPEED_STOP)
        self.logger.info(f"moving right backward at {speed}")
        # self.setESC(self.thrusterFR, speed2)
        self.setESC(self.thrusterBR, speed)

    def moveForward(self, speed): 
        self.logger.info(f"moving forward at {speed}")

        speed2 = SPEED_STOP - (speed - SPEED_STOP)
        # calculate speed for reverse thrusters
        self.setESC(self.thrusterFR, speed)
        self.setESC(self.thrusterFL, speed2)
        self.setESC(self.thrusterBR, speed2)
        self.setESC(self.thrusterBL, speed2)
       

    def moveBackward(self, speed):
        # calculate speed for reverse thrusters
        speed2 = SPEED_STOP - (speed - SPEED_STOP)
        self.logger.info(f"moving backward at {speed2}")
        self.setESC(self.thrusterFR, speed2)
        self.setESC(self.thrusterFL, speed)
        self.setESC(self.thrusterBR, speed)
        self.setESC(self.thrusterBL, speed)

    def rotateRight(self, speed):
        # calculate spped for
        speed2 = SPEED_STOP - (speed - SPEED_STOP)
        self.logger.info(f"moving backward at {speed}")
        self.setESC(self.thrusterFL, speed2)
        self.setESC(self.thrusterFR, speed2)
        self.setESC(self.thrusterBL, speed2)
        self.setESC(self.thrusterBR, speed)

    def rotateLeft(self, speed):
        # calculate spped for
        speed2 = SPEED_STOP - (speed - SPEED_STOP)
        self.logger.info(f"moving backward at {speed}")
        self.setESC(self.thrusterFL, speed)
        self.setESC(self.thrusterFR, speed)
        self.setESC(self.thrusterBL, speed)
        self.setESC(self.thrusterBR, speed2)

    def strafeRight(self, speed):
        print("Test: inside Strafe right");
        speed2 = SPEED_STOP - (speed - SPEED_STOP)
        self.logger.info(f"strafing at {speed}")
        self.setESC(self.thrusterBR, speed2-50)
        self.setESC(self.thrusterBL, speed+50)
        self.setESC(self.thrusterFR, speed2)
        self.setESC(self.thrusterFL, speed2)

    def strafeLeft(self, speed):
        print("Test: inside Strafe left");
        speed2 = SPEED_STOP - (speed - SPEED_STOP)
        self.logger.info(f"strafing at {speed}")
        self.setESC(self.thrusterBR, speed+25)
        self.setESC(self.thrusterBL, speed2-25)
        self.setESC(self.thrusterFR, speed)
        self.setESC(self.thrusterFL, speed)

    def strafeStop(self, speed):
        print("Test: inside Strafe left");
        speed2 = SPEED_STOP - (speed - SPEED_STOP)
        self.logger.info(f"strafing at {speed}")
        self.setESC(self.thrusterFR, 1500)
        self.setESC(self.thrusterFL, 1500)
        self.setESC(self.thrusterBR, 1500)
        self.setESC(self.thrusterBL, 1500)
       

        # for autonomous movement :o
        # if duration > 0:
        #     time.sleep(duration)
        #     self.setESC(self.thrusterFL, SPEED_STOP)
        #     self.setESC(self.thrusterBL, SPEED_STOP)
        #     self.setESC(self.thrusterFR, SPEED_STOP)
        #     self.setESC(self.thrusterBR, SPEED_STOP)

    # def rotateLeft(self, speed):
    #     self.logger.info(f"rotating left at {speed}")
    #     speed2 = SPEED_STOP - (speed - SPEED_STOP)
    #     self.setESC(self.thrusterFL, speed)
    #     self.setESC(self.thrusterBR, speed)

    # def rotateRight(self, speed):
    #     self.logger.info(f"rotating right at {speed}")
    #     speed2 = SPEED_STOP - (speed - SPEED_STOP)
    #     self.setESC(self.thrusterBL, speed)
    #     self.setESC(self.thrusterFR, speed)

    def moveDown(self, duration = 0):
        try:
            # self.logger.info(f"going up at {SPEED_STOP - self.variableSpeed}")
            self.setESC(self.thrusterVL, int(SPEED_STOP + self.variableSpeed))
            self.setESC(self.thrusterVR, int(SPEED_STOP - self.variableSpeed))
            print(f"moveDown: {int(SPEED_STOP - self.variableSpeed)}")

            # for autonomous movement :o
            # if duration > 0:
            #     time.VLeep(duration)
            #     self.setESC(self.thrusterVL, SPEED_STOP)
            #     self.setESC(self.thrusterVR, SPEED_STOP)
        except Exception as e:
            print(f"Exception: {e}")

    def moveUp(self, duration = 0):
        try:
            # self.logger.info(f"going down at {SPEED_STOP + self.variableSpeed}")
            self.setESC(self.thrusterVL, int(SPEED_STOP - self.variableSpeed))
            self.setESC(self.thrusterVR, int(SPEED_STOP + self.variableSpeed))
            print(f"moveUp: {int(SPEED_STOP + self.variableSpeed)}")
        except Exception as e:
            print(f"Exception: {e}")

    def noMoveUpDown(self):
        try:
            self.setESC(self.thrusterVL, int(SPEED_STOP))
            self.setESC(self.thrusterVR, int(SPEED_STOP))
            print(f"Up and down thrusters have stopped: {int(SPEED_STOP)}")
        except Exception as e:
            print(f"Exception: {e}")
        # for autonomous movement :o
        # if duration > 0:
        #     time.sleep(duration)
        #     self.setESC(self.thrusterVL, SPEED_STOP)
        #     self.setESC(self.thrusterVR, SPEED_STOP)

    def atonDock(self):
        self.setESC(self.thrusterFL, 1700)
        self.setESC(self.thrusterFR, 1700)
        time.sleep(5)

    def stop(self):
        self.ps4Model = PS4Model()
        self.logger.info("stop")
        self.setESC(self.thrusterBL, SPEED_STOP)
        self.setESC(self.thrusterBR, SPEED_STOP)
        self.setESC(self.thrusterFR, SPEED_STOP)
        self.setESC(self.thrusterFL, SPEED_STOP)
        self.setESC(self.thrusterVL, SPEED_STOP)
        self.setESC(self.thrusterVR, SPEED_STOP)

    # def FL_OFF(self):
    #     self.logger.info("Electro-Magnet Off")
    #     self.setPT(self.flashLight, RELAY_OFF)

    # def FL_ON(self):
    #     self.logger.info("Electro-Magnet On")
    #     self.setPT(self.flashLight, RELAY_ON)
    
    def CLAW_OPEN(self):
        self.logger.info("Claw is open")
        self.CLAW_OFF()
        time.sleep(.2)
        self.setPT(self.clawOpenONE, RELAY_ON)
        self.setPT(self.clawOpenTWO, RELAY_ON)

    def CLAW_CLOSE(self):
        self.logger.info("Claw is closed")
        self.CLAW_OFF()
        time.sleep(.2)
        self.setPT(self.clawCloseONE, RELAY_ON)
        self.setPT(self.clawCloseTWO, RELAY_ON)
    
    def CLAW_OFF(self):
        self.logger.info("Claw is off")
        self.setPT(self.clawOpenONE, RELAY_OFF)
        self.setPT(self.clawOpenTWO, RELAY_OFF)
        self.setPT(self.clawCloseONE, RELAY_OFF)
        self.setPT(self.clawCloseTWO, RELAY_OFF)

    # def CLAW_ON(self):
    #     self.logger.info("Claw is on")
    #     self.setPT(self.clawOpenONE, RELAY_ON)
    #     self.setPT(self.clawOpenTWO, RELAY_ON)
    #     self.setPT(self.clawCloseONE, RELAY_ON)
    #     self.setPT(self.clawCloseTWO, RELAY_ON)

    # def INIT_RELAYS(self):
    #     self.logger.info("Initializing relays")
    #     self.clear() # turn off claw and flashlight relays
    #     time.sleep(2)
    #     self.setPT(self.relays, RELAY_OFF)

    def rotateClaw(self, val):
        self.logger.info("Claw is rotating")
        self.clawRotate(self.clawRT, val)
        time.sleep(1.5)

    def Rotate35(self):
        self.logger.info("THe Claw Rotated 35 Degrees")
        self.clawRotate(self.clawRT, 35)

    def Rotate65(self):
        self.logger.info("THe Claw Rotated 65 Degrees")
        self.clawRotate(self.clawRT, 65)

    def Rotate90(self):
        self.logger.info("THe Claw Rotated 90 Degrees")
        self.clawRotate(self.clawRT, 90)

    def Rotate165(self):
        self.logger.info("THe Claw Rotated 115 Degrees")
        self.clawRotate(self.clawRT, 165)

    # def autoMove(self, model: AutonomousMovement):
    #     direction = model["direction"]
    #     x = model["x"]
    #     y = model["y"]
    #     speed = model["speed"]
    #     duration = model["duration"]

    #     if direction == DIRECTION.RIGHT:
    #         self.strafeRight(speed, duration)
    #     elif direction == DIRECTION.LEFT:
    #         self.strafeLeft(speed, duration)
    #     elif direction == DIRECTION.UP:
    #         self.moveUp(speed, duration)
    #     elif direction == DIRECTION.DOWN:
    #         self.moveDown(speed, duration)

    def test(self):
        time.sleep(2)
        self.setESC(self.thrusterFR, SPEED_STOP)
        time.sleep(2)
        self.setESC(self.thrusterFR, SPEED_MAX)
        time.sleep(2)
        self.setESC(self.thrusterFR, SPEED_STOP)

if __name__ == '__main__':
    i = 1 
