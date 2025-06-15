import serial
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation

# === CONFIGURACIÓN ===
puerto = 'COM4'         
baudrate = 115200
fs = 2160               # Frecuencia de muestreo (igual al delayMicroseconds en Arduino)
N = 512                 # Número de muestras para la FFT (potencia de 2)

# === CONECTAR AL PUERTO SERIAL ===
ser = serial.Serial(puerto, baudrate, timeout=1)

# === FUNCIONES DE ACTUALIZACIÓN ===
def leer_datos(n):
    datos = []
    while len(datos) < n:
        try:
            linea = ser.readline().decode('utf-8').strip()
            if linea.isdigit():
                valor = int(linea)
                datos.append(valor)
        except:
            pass
    return np.array(datos)

def actualizar(frame):
    datos = leer_datos(N)
    datos = datos - np.mean(datos)  # Eliminar DC
    fft_vals = np.fft.fft(datos)
    freqs = np.fft.fftfreq(N, 1/fs)
    magnitud = np.abs(fft_vals)[:N//2]
    freqs = freqs[:N//2]

    linea.set_data(freqs, magnitud)
    ax.set_xlim(0, 150)
    ax.set_ylim(0, np.max(magnitud)*1.1)
    return linea,

# === PLOTEO ===
fig, ax = plt.subplots()
linea, = ax.plot([], [], lw=2)
ax.set_title("FFT en Tiempo Real")
ax.set_xlabel("Frecuencia (Hz)")
ax.set_ylabel("Magnitud")

ani = FuncAnimation(fig, actualizar, interval=100)
plt.tight_layout()
plt.show()
