# pyinstaller --onefile --windowed "/home/notebook/Área de trabalho/Programas/newenv/ClimaX1585en.py"
## Credit to Guizz1585
### Contribua com testes e atualizações
#### reddit.com/user/GLeme1/
##### github.com/guizz1585/

import sys
import time
import serial
import serial.tools.list_ports
from PyQt5.QtWidgets import (
    QApplication, QLabel, QVBoxLayout, QWidget, QPushButton, QSlider,
    QMessageBox, QComboBox, QGroupBox, QFormLayout, QHBoxLayout
)
from PyQt5.QtCore import QThread, pyqtSignal, Qt
import logging

# Function to detect available serial ports
def detect_ports():
    ports = serial.tools.list_ports.comports()
    return [port.device for port in ports]

# Logger configuration
logging.basicConfig(filename='climate_control.log', level=logging.INFO,
                    format='%(asctime)s - %(levelname)s - %(message)s')

# Sensor classes
class TemperatureSensor:
    def __init__(self, port):
        self.ser = serial.Serial(port, 9600, timeout=1)

    def read_temperature(self):
        try:
            self.ser.write(b'TEMP\n')
            temp = self.ser.readline().decode().strip()
            return float(temp) if temp else 25.0  # Default value if failure
        except Exception as e:
            logging.error(f"Error reading temperature: {e}")
            return 25.0

class HumiditySensor:
    def __init__(self, port):
        self.ser = serial.Serial(port, 9600, timeout=1)

    def read_humidity(self):
        try:
            self.ser.write(b'HUMID\n')
            humidity = self.ser.readline().decode().strip()
            return float(humidity) if humidity else 45.0  # Default value if failure
        except Exception as e:
            logging.error(f"Error reading humidity: {e}")
            return 45.0

class LightSensor:
    def __init__(self, port):
        self.ser = serial.Serial(port, 9600, timeout=1)

    def read_light_level(self):
        try:
            self.ser.write(b'LIGHT\n')
            light_level = self.ser.readline().decode().strip()
            return int(light_level) if light_level else 500  # Default value if failure
        except Exception as e:
            logging.error(f"Error reading light level: {e}")
            return 500

# Climate control thread class
class ClimateControlThread(QThread):
    update_data = pyqtSignal(str, str, str)
    alert_signal = pyqtSignal(str)

    def __init__(self, ports):
        super().__init__()
        self.temp_sensor = TemperatureSensor(ports[0])
        self.humidity_sensor = HumiditySensor(ports[1])
        self.light_sensor = LightSensor(ports[2])
        self.target_temp = 25
        self.target_humidity = 50
        self.target_light = 500
        self.rain_threshold = 50
        self.light_min = 400
        self.running = True

        # Control devices
        self.devices = {
            "rain": serial.Serial(ports[3], 9600, timeout=1),
            "humidifier": serial.Serial(ports[4], 9600, timeout=1),
            "intake": serial.Serial(ports[5], 9600, timeout=1),
            "exhaust": serial.Serial(ports[6], 9600, timeout=1),
            "light": serial.Serial(ports[7], 9600, timeout=1)
        }

    def run(self):
        while self.running:
            temp = self.temp_sensor.read_temperature()
            humidity = self.humidity_sensor.read_humidity()
            light_level = self.light_sensor.read_light_level()

            self.control_devices(temp, humidity, light_level)

            self.update_data.emit(
                f"Temperature: {temp:.2f}°C",
                f"Humidity: {humidity:.2f}%",
                f"Light Level: {light_level} lux"
            )

            logging.info(f"Temperature: {temp}, Humidity: {humidity}, Light Level: {light_level}")

            time.sleep(5)

    def control_devices(self, temp, humidity, light_level):
        # Temperature control
        if temp < self.target_temp:
            self.devices["intake"].write(b'ON\n')  # Turn on intake
        else:
            self.devices["intake"].write(b'OFF\n')

        if temp > self.target_temp:
            self.devices["exhaust"].write(b'ON\n')  # Turn on exhaust
        else:
            self.devices["exhaust"].write(b'OFF\n')

        # Humidity control
        if humidity < self.target_humidity:
            self.devices["humidifier"].write(b'ON\n')  # Turn on humidifier
        else:
            self.devices["humidifier"].write(b'OFF\n')

        # Artificial rain control with additional conditions
        if (humidity < self.rain_threshold and 
            light_level <= self.light_min and 
            temp >= 18):
            self.devices["rain"].write(b'ON\n')  # Turn on artificial rain
        else:
            self.devices["rain"].write(b'OFF\n')

        # Light control
        if light_level < self.target_light:
            self.devices["light"].write(b'ON\n')  # Turn on light
        else:
            self.devices["light"].write(b'OFF\n')

    def set_targets(self, temp, humidity, light):
        self.target_temp = temp
        self.target_humidity = humidity
        self.target_light = light

    def set_rain_threshold(self, threshold):
        self.rain_threshold = threshold

    def set_light_min(self, light_min):
        self.light_min = light_min

    def stop(self):
        self.running = False
        logging.info("Climate control stopped.")

# GUI class
class ClimateControlApp(QWidget):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("guizz1585@gmail.com")
        self.setGeometry(100, 100, 600, 550)
        self.setStyleSheet("background-color: #f0f4f8; font-family: Arial, sans-serif;")

        layout = QVBoxLayout()
        layout.setSpacing(15)
        layout.setContentsMargins(20, 20, 20, 20)

        # Labels to display data
        self.temp_label = QLabel("Temperature: --°C")
        self.humidity_label = QLabel("Humidity: --%")
        self.light_label = QLabel("Light Level: -- lux")

        # Climate control section
        control_group = QGroupBox("Climate Settings")
        control_layout = QFormLayout()

        self.temp_label_slider, self.temp_slider = self.create_slider("Target Temperature (°C):", 25, 15, 35)
        self.humidity_label_slider, self.humidity_slider = self.create_slider("Target Humidity (%):", 50, 30, 100)
        self.light_label_slider, self.light_slider = self.create_slider("Target Light Level (lux):", 500, 0, 1000)

        control_layout.addRow(self.temp_label_slider, self.temp_slider)
        control_layout.addRow(self.humidity_label_slider, self.humidity_slider)
        control_layout.addRow(self.light_label_slider, self.light_slider)

        control_group.setLayout(control_layout)
        layout.addWidget(control_group)

        # USB port selection section
        port_group = QGroupBox("Select USB Ports for Devices")
        port_layout = QFormLayout()
        self.port_selectors = []

        available_ports = detect_ports()
        for i in range(8):
            port_selector = QComboBox()
            port_selector.addItems(available_ports)
            port_layout.addRow(f"Device {i + 1}:", port_selector)
            self.port_selectors.append(port_selector)

        port_group.setLayout(port_layout)
        layout.addWidget(port_group)

        # Presets section
        preset_group = QGroupBox("Preset Selection")
        preset_layout = QHBoxLayout()
        self.preset_selector = QComboBox()
        self.preset_selector.addItems(["Manual", "Day", "Night", "Morning/Afternoon", "Tropical", "Dry", "Storm"])
        self.preset_selector.currentIndexChanged.connect(self.update_presets)
        preset_layout.addWidget(self.preset_selector)
        preset_group.setLayout(preset_layout)
        layout.addWidget(preset_group)

        # Artificial rain control section
        rain_control_group = QGroupBox("Artificial Rain Settings")
        rain_control_layout = QFormLayout()
        self.rain_threshold_label, self.rain_threshold_slider = self.create_slider("Humidity for Artificial Rain (%):", 50, 0, 100)
        self.light_min_label, self.light_min_slider = self.create_slider("Minimum Light for Artificial Rain (lux):", 400, 0, 1000)

        rain_control_layout.addRow(self.rain_threshold_label, self.rain_threshold_slider)
        rain_control_layout.addRow(self.light_min_label, self.light_min_slider)
        rain_control_group.setLayout(rain_control_layout)
        layout.addWidget(rain_control_group)

        # Control buttons
        button_layout = QHBoxLayout()
        self.start_button = self.create_button("Start Climate Control", self.start_climate_control)
        self.stop_button = self.create_button("Stop Control", self.stop_control)

        button_layout.addWidget(self.start_button)
        button_layout.addWidget(self.stop_button)

        layout.addLayout(button_layout)
        layout.addWidget(self.temp_label)
        layout.addWidget(self.humidity_label)
        layout.addWidget(self.light_label)

        self.setLayout(layout)
        self.control_thread = None

    def create_button(self, text, function):
        button = QPushButton(text)
        button.clicked.connect(function)
        button.setStyleSheet("""
            background-color: #3498db; color: white; padding: 10px;
            border: none; border-radius: 5px;
        """)
        return button

    def create_slider(self, label_text, initial_value, min_value, max_value):
        label = QLabel(f"{label_text} {initial_value}")
        slider = QSlider(Qt.Horizontal)
        slider.setRange(min_value, max_value)
        slider.setValue(initial_value)
        slider.setStyleSheet("""
            QSlider::groove:horizontal {
                background: #dfe6e9; height: 10px; border-radius: 5px;
            }
            QSlider::handle:horizontal {
                background: #3498db; width: 15px; height: 15px; border-radius: 5px;
            }
        """)
        slider.valueChanged.connect(lambda value: label.setText(f"{label_text} {value}"))
        return label, slider

    def start_climate_control(self):
        selected_ports = [selector.currentText() for selector in self.port_selectors]
        if len(set(selected_ports)) != 8:
            QMessageBox.critical(self, "Error", "Select different ports for each device!")
            return

        self.control_thread = ClimateControlThread(selected_ports)
        self.control_thread.update_data.connect(self.update_display)
        self.control_thread.alert_signal.connect(self.display_alert)

        temp = self.temp_slider.value()
        humidity = self.humidity_slider.value()
        light = self.light_slider.value()

        self.control_thread.set_targets(temp, humidity, light)
        self.control_thread.set_rain_threshold(self.rain_threshold_slider.value())
        self.control_thread.set_light_min(self.light_min_slider.value())

        self.control_thread.start()
        logging.info("Climate control started.")

    def stop_control(self):
        if self.control_thread:
            self.control_thread.stop()
            self.control_thread.wait()
            logging.info("Climate control stopped.")

    def update_display(self, temp, humidity, light):
        self.temp_label.setText(temp)
        self.humidity_label.setText(humidity)
        self.light_label.setText(light)

    def update_presets(self, index):
        presets = [
            (25, 50, 500),
            (30, 40, 1000),
            (18, 60, 200),
            (22, 70, 800),
            (28, 80, 900),
            (26, 20, 400),
            (24, 90, 300)
        ]
        preset = presets[index]
        self.temp_slider.setValue(preset[0])
        self.humidity_slider.setValue(preset[1])
        self.light_slider.setValue(preset[2])

    def display_alert(self, message):
        QMessageBox.warning(self, "Alert", message)

# Main function
if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = ClimateControlApp()
    window.show()
    sys.exit(app.exec_())




                                                                                # Jesus #