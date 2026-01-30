import Rover1.ministries.control.motor as m
import Rover1.ministries.arduino.commands as c

print("motor.apply_motor_command =", m.apply_motor_command)
print("type =", type(m.apply_motor_command))

print("arduino_commands.send_arduino_command =", c.send_arduino_command)
print("type =", type(c.send_arduino_command))
