import time
import matplotlib.pyplot as plt

from temperature_sensor.temp_sens import TempSensor
from temperature_sensor.task_timer import TaskTimer

gain = 1
samples_per_second = 32
temp_sens = TempSensor(gain, samples_per_second)

task_measure = TaskTimer(1, temp_sens.measure_and_update)
task_measure.start()

time.sleep(30)

task_measure.stop()

plt.plot(temp_sens.xs, temp_sens.ys)
plt.yscale("linear")
plt.ylabel("Temperature (°C)")
plt.xlabel("Time (s)")
plt.show()
