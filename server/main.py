from temperature_sensor.temp_sens import TempSensor

gain = 1
samples_per_second = 64
adc_channel_0 = 0
temp_sens = TempSensor(gain, samples_per_second)

# Task: Control the steppermotor based on our temperature
# T <= 25 °C = The motor is moved by 0 degrees
# 25 °C < T < 30 °C = The motor is moved by 10 - 80 degrees
# T >= 30 °C = The motor is moved by 90 degrees
