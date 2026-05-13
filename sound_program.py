import math
import time
import struct
import pyaudio

# --- CONFIGURACIÓN ---
FRECUENCIA = 440       # Frecuencia en Hz (Nota LA)
PORCENTAJE_VOLUMEN = 80  # Variable de volumen: define el porcentaje (0 a 100)
RATE = 44100            # Tasa de muestreo (Calidad de CD)
CHANNELS = 2            # CONFIGURACIÓN MANDATORIA: 2 Canales para Estéreo
INTERVALO = 5.0        # Tiempo en segundos para alternar de lado

# Conversión del porcentaje a factor de amplitud (rango de 0.0 a 1.0)
volumen_clamped = max(0, min(100, PORCENTAJE_VOLUMEN))
AMPLITUD = volumen_clamped / 100.0

# Inicializar PyAudio
p = pyaudio.PyAudio()

# Abrir el flujo de salida en estéreo
stream = p.open(
    format=pyaudio.paFloat32,
    channels=CHANNELS,
    rate=RATE,
    output=True
)

print(f"Generando tono de {FRECUENCIA}Hz al {volumen_clamped}% de volumen...")
print(f"Alternando canales (Izquierda / Derecha) cada {INTERVALO} segundos.")

try:
    chunk_size = 1024
    fase = 0.0
    omega = 2.0 * math.pi * FRECUENCIA / RATE
    tiempo_inicio = time.time()

    while True:
        # Calcular el tiempo transcurrido para determinar el canal activo
        tiempo_actual = time.time() - tiempo_inicio
        ciclo_actual = int(tiempo_actual / INTERVALO)
        
        # Si el ciclo es par, suena Izquierda. Si es impar, suena Derecha.
        izq_activo = (ciclo_actual % 2 == 0)

        samples = []
        for _ in range(chunk_size):
            sample_base = AMPLITUD * math.sin(fase)
            
            # En estéreo se envían las muestras entrelazadas: [Izquierda, Derecha, Izquierda, Derecha...]
            if izq_activo:
                samples.append(sample_base)  # Canal Izquierdo con sonido
                samples.append(0.0)          # Canal Derecho en silencio
            else:
                samples.append(0.0)          # Canal Izquierdo en silencio
                samples.append(sample_base)  # Canal Derecho con sonido
                
            fase += omega
            if fase >= 2.0 * math.pi:
                fase -= 2.0 * math.pi
        
        # Empaquetar el doble de muestras (2 por cada ciclo del buffer debido al estéreo)
        data = struct.pack(f'{chunk_size * CHANNELS}f', *samples)
        
        # Enviar el bloque de audio a la salida física
        stream.write(data)

except KeyboardInterrupt:
    print("\nDeteniendo señal de audio...")

finally:
    # Cierre seguro de las conexiones de audio
    stream.stop_stream()
    stream.close()
    p.terminate()
