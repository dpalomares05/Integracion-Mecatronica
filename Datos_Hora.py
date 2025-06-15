import serial
import time
import csv
from datetime import datetime

# Configuración
PORT = 'COM4'  # Cambia esto según tu sistema
BAUD_RATE = 115200
DURATION_SECONDS = 3600
THRESHOLD = 512  # Umbral aproximado para cruce por cero
CSV_FILE = 'Frecuencia_Zmpt101b.csv'

def detectar_cruces_por_cero(valores):
    cruces = 0
    for i in range(1, len(valores)):
        if (valores[i-1] < THRESHOLD and valores[i] >= THRESHOLD) or \
           (valores[i-1] > THRESHOLD and valores[i] <= THRESHOLD):
            cruces += 1
    return cruces


def calcular_frecuencia(cruces, tiempo_segundos):
    ciclos = cruces / 2  # 2 cruces por ciclo
    frecuencia = ciclos / tiempo_segundos
    return round(frecuencia, 3)

def main():
    try:
        ser = serial.Serial(PORT, BAUD_RATE, timeout=1)
        print("Conectado a", PORT)
        time.sleep(2)  # Esperar al inicio

        with open(CSV_FILE, mode='w', newline='') as file:
            writer = csv.writer(file)
            writer.writerow(['timestamp', 'frecuencia_Hz'])

            for _ in range(DURATION_SECONDS):
                start_time = time.time()
                buffer = []

                while time.time() - start_time < 1.0:
                    try:
                        line = ser.readline().decode().strip()
                        if line.isdigit():
                            buffer.append(int(line))
                    except:
                        continue

                cruces = detectar_cruces_por_cero(buffer)
                frecuencia = calcular_frecuencia(cruces, 1.0)
                timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                writer.writerow([timestamp, frecuencia])
                print(f"{timestamp} - Frecuencia: {frecuencia} Hz")

    except serial.SerialException as e:
        print("Error con el puerto serie:", e)
    finally:
        if 'ser' in locals() and ser.is_open:
            ser.close()
        print("Lectura finalizada.")

if __name__ == "__main__":
    main()
