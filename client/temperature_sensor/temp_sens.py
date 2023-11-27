import Adafruit_ADS1x15
import numpy as np


class TempSensor:
    def __init__(self, gain, samples_per_second):
        self.adc = Adafruit_ADS1x15.ADS1115()  # Create an ADS1115 ADC (16-bit) instance
        self.adc_channel = 0
        self.raw_data = None
        self.voltage_measurements = None
        self.gain = gain  # Set the gain to 1
        self.samples_per_second = samples_per_second  # Set the samples per second to 64
        self.xs = []  # Create empty lists for our x values
        self.ys = []  # Create empty lists for our y values

    # Function to measure the temperature
    def measure_temp(self):
        # Read the ADC
        self.raw_data = self.adc.read_adc(self.adc_channel, self.gain, self.samples_per_second)

        # Convert the ADC value to a voltage
        self.voltage_measurements = float(self.raw_data) / 32767.0 * 4.095
        print(self.voltage_measurements)

        # Saving constants for our equation, which we'll be using later
        __A = 0.001129148  # 0.001129148 is the A constant of our steinhart-hart equation
        __B = 0.000234125  # 0.000234125 is the B constant of our steinhart-hart equation
        __C = 0.0000000876741  # 0.0000000876741 is the C constant of our steinhart-hart equation

        # Fixed values thermistor
        __RES = 10000  # 10 kΩ is the resistance of the thermistor
        __VOLT = 3.3  # 3.3 V is the voltage of our thermistor

        # Calculate the temperature based on our voltage values by using the steinhart-hart equation
        temp = __RES / (__VOLT / self.voltage_measurements - 1)
        temp = 1 / (__A + __B * np.log(temp) + __C * np.power(np.log(temp), 3))
        temp = temp - 273.15  # Translate from Kelvin to Celsius

        # Round the temperature to 2 decimal places for readability
        temp = round(temp, 2)

        return temp

    # Update data to our lists
    def update_data(self, temp):
        # Add '1' if nothing is in our list
        if not self.xs:
            self.xs.append(1)
        # Add '1' to our last entry in our list
        else:
            self.xs.append(self.xs[-1] + 1)
        # Add our temperature value to our list
        self.ys.append(temp)

    # Measure the temperature and update our lists
    def measure_and_update(self):
        temp = self.measure_temp()
        self.update_data(temp)
