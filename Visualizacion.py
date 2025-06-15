import sys
import serial
import time
from PyQt5 import QtWidgets, QtGui
from PyQt5 import QtCore
from pyqtgraph import PlotWidget
import pyqtgraph as pg
import numpy as np
from collections import deque
from threading import Thread

# Configura tu puerto correctamente
PORT = 'COM4'  # O '/dev/ttyUSB0' en Linux
BAUD_RATE = 115200
SAMPLE_WINDOW = 500  # Número de muestras mostradas

class SensorApp(QtWidgets.QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Monitor ZMPT101B")
        self.setGeometry(100, 100, 1000, 600)

        # Layouts principales
        main_layout = QtWidgets.QHBoxLayout(self)
        left_layout = QtWidgets.QVBoxLayout()
        right_layout = QtWidgets.QVBoxLayout()

        # Widgets de gráficas
        self.volt_plot = PlotWidget(title="Voltaje")
        self.freq_plot = PlotWidget(title="Frecuencia")

        self.volt_plot.setYRange(0, 1023)
        self.volt_curve = self.volt_plot.plot(pen='c', symbol='o', symbolSize=2)

        self.freq_plot.setYRange(55, 65)
        self.freq_curve = self.freq_plot.plot(pen='y')

        left_layout.addWidget(self.volt_plot)
        left_layout.addWidget(self.freq_plot)

        # Estado visual
        self.status_label = QtWidgets.QLabel("Estado Actual:")
        self.status_text = QtWidgets.QLabel("Esperando datos...")

        # Mostrar frecuencia actual
        self.freq_label = QtWidgets.QLabel("Frecuencia actual: --- Hz")
        right_layout.addWidget(self.freq_label)

        # Botón para exportar CSV
        self.export_button = QtWidgets.QPushButton("Exportar CSV")
        self.export_button.clicked.connect(self.export_csv)
        right_layout.addWidget(self.export_button)


        self.led_red = QtWidgets.QLabel()
        self.led_yellow = QtWidgets.QLabel()
        self.led_green = QtWidgets.QLabel()

        for led in [self.led_red, self.led_yellow, self.led_green]:
            led.setFixedSize(20, 20)
            led.setStyleSheet("background-color: gray; border: 1px solid black;")

        icon_layout = QtWidgets.QHBoxLayout()
        icon_layout.addWidget(self.led_red)
        icon_layout.addWidget(self.led_yellow)
        icon_layout.addWidget(self.led_green)
        icon_layout.addWidget(self.status_text)

        right_layout.addWidget(self.status_label)
        right_layout.addLayout(icon_layout)
        right_layout.addStretch()

        # Añadir layouts al principal
        main_layout.addLayout(left_layout, 3)
        main_layout.addLayout(right_layout, 1)

        # Datos
        self.volt_data = deque(maxlen=SAMPLE_WINDOW)
        self.freq_data = deque(maxlen=100)
        self.timestamps = deque(maxlen=SAMPLE_WINDOW)

        # Serial y lectura
        self.serial = serial.Serial(PORT, BAUD_RATE, timeout=1)
        self.running = True
        self.last_zero_cross = None
        self.freq_buffer = deque(maxlen=10)

        self.thread = Thread(target=self.read_serial)
        self.thread.start()

        # Timer para actualizar GUI
        self.timer = QtCore.QTimer()
        self.timer.timeout.connect(self.update_plot)
        self.timer.start(50)

    def read_serial(self):
        while self.running:
            try:
                line = self.serial.readline().decode().strip()
                if line.isdigit():
                    value = int(line)
                    now = time.time()
                    self.volt_data.append(value)
                    self.timestamps.append(now)

                    # Frecuencia por cruce por cero
                    if len(self.volt_data) >= 2:
                        if self.volt_data[-2] < 512 and value >= 512:
                            if self.last_zero_cross is not None:
                                period = now - self.last_zero_cross
                                freq = 1.0 / period if period > 0 else 0
                                self.freq_buffer.append(freq)
                            self.last_zero_cross = now
            except Exception as e:
                print("Error:", e)

    def update_plot(self):
        # Actualizar gráfica de voltaje
        if len(self.volt_data) > 0:
            x = np.arange(len(self.volt_data))
            y = np.array(self.volt_data)
            self.volt_curve.setData(x, y)

        # Calcular y actualizar frecuencia
        avg_freq = 0
        if len(self.freq_buffer) > 0:
            avg_freq = np.mean(self.freq_buffer)
            self.freq_data.append(avg_freq)
            self.freq_curve.setData(np.arange(len(self.freq_data)), list(self.freq_data))

        # Verificar estado
        if len(self.volt_data) > 10:
            variation = max(self.volt_data) - min(self.volt_data)
            signal_flat = variation < 5
            freq_out_of_range = avg_freq < 55 or avg_freq > 65

            if signal_flat and freq_out_of_range:
                self.set_status("Frecuencia fuera de rango y sensor no leyendo", "amarillo + rojo")
                self.update_leds(red=True, yellow=True)
            elif signal_flat:
                self.set_status("Sensor no leyendo", "rojo")
                self.update_leds(red=True)
            elif freq_out_of_range:
                self.set_status("Frecuencia fuera de rango", "amarillo")
                self.update_leds(yellow=True)
            else:
                self.set_status("Sensor leyendo correctamente", "verde")
                self.update_leds(green=True)
        else:
            self.set_status("Sensor no leyendo", "rojo")
            self.update_leds(red=True)

        if len(self.freq_buffer) > 0:
            avg_freq = np.mean(self.freq_buffer)
            self.freq_data.append(avg_freq)
            self.freq_curve.setData(np.arange(len(self.freq_data)), list(self.freq_data))
            self.freq_label.setText(f"Frecuencia actual: {avg_freq:.3f} Hz")


    def update_leds(self, red=False, yellow=False, green=False):
        self.led_red.setStyleSheet(f"background-color: {'red' if red else 'gray'}; border: 1px solid black;")
        self.led_yellow.setStyleSheet(f"background-color: {'yellow' if yellow else 'gray'}; border: 1px solid black;")
        self.led_green.setStyleSheet(f"background-color: {'green' if green else 'gray'}; border: 1px solid black;")

    def set_status(self, message, _):
        self.status_text.setText(message)

    def closeEvent(self, event):
        self.running = False
        self.serial.close()
        event.accept()
    
    def export_csv(self):
        try:
            filename, _ = QtWidgets.QFileDialog.getSaveFileName(self, "Guardar como", "", "CSV Files (*.csv)")
            if filename:
                with open(filename, 'w') as f:
                    f.write("Timestamp,Voltaje,Frecuencia\n")
                    for i in range(min(len(self.timestamps), len(self.volt_data))):
                        timestamp = self.timestamps[i]
                        volt = self.volt_data[i]
                        freq = self.freq_data[i] if i < len(self.freq_data) else ''
                        f.write(f"{timestamp},{volt},{freq}\n")
                QtWidgets.QMessageBox.information(self, "Éxito", "Datos exportados correctamente.")
        except Exception as e:
            QtWidgets.QMessageBox.critical(self, "Error", f"No se pudo exportar el archivo.\n{e}")


if __name__ == '__main__':
    app = QtWidgets.QApplication(sys.argv)
    win = SensorApp()
    win.show()
    sys.exit(app.exec_())
