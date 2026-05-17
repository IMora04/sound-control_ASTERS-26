import math
import time
import random
import struct
import pyaudio

# ─────────────────────────────────────────────
#  CONFIGURACIÓN  ── edita aquí
# ─────────────────────────────────────────────
#
#  Formato por canal:
#    { frecuencia_hz: (vol_min_%, vol_max_%) }
#
#  Puedes añadir tantas frecuencias como quieras.

CHANNEL = {   # RECIPIENTE GRANDE
     20: (10, 50),
     30: (10,  60),
     40: (5,  25),
     50: (10,  45),
     60: (0, 0),
     80: (0, 0),
    100: (0, 0),
    150: (0, 0),
    250: (0, 0),
    350: (0, 0),
    450: (0, 0),
    550: (0, 0),
}

# Cuántos segundos dura cada tono antes de elegir uno nuevo
DURACION_TONO = 5.0      # segundos

# ─────────────────────────────────────────────
RATE       = 44100
CHANNELS   = 2
CHUNK      = 1024
# ─────────────────────────────────────────────


def pick_tone(channel_config: dict) -> tuple:
    """Devuelve (frecuencia, amplitud) aleatorios del canal dado."""
    freq = random.choice(list(channel_config.keys()))
    vol_min, vol_max = channel_config[freq]
    pct = random.uniform(vol_min, vol_max)
    amp = max(0.0, min(1.0, pct / 100.0))
    return float(freq), amp


def main():
    p = pyaudio.PyAudio()
    stream = p.open(
        format=pyaudio.paFloat32,
        channels=CHANNELS,
        rate=RATE,
        output=True,
    )

    print("Iniciando generador binaural con frecuencias aleatorias.")
    print(f"Cada {DURACION_TONO} s se elige una nueva frecuencia por canal.\n")

    try:
        # Estado inicial para cada canal
        freq_L, amp_L = pick_tone(CHANNEL)
        omega_L = 2.0 * math.pi * freq_L / RATE
        fase_L = fase_R = 0.0

        ultimo_cambio = time.time()
        print(f"   {freq_L:.1f} Hz @ {amp_L*100:.1f}%")

        while True:
            ahora = time.time()

            # ¿Toca elegir nuevas frecuencias?
            if ahora - ultimo_cambio >= DURACION_TONO:
                freq_L, amp_L = pick_tone(CHANNEL)
                omega_L = 2.0 * math.pi * freq_L / RATE
                ultimo_cambio = ahora
                print(f"  Izq: {freq_L:.1f} Hz @ {amp_L*100:.1f}%   ")

            # Generar bloque de muestras entrelazadas [L, R, L, R, …]
            samples = []
            for _ in range(CHUNK):
                samples.append(amp_L * math.sin(fase_L))   # canal izquierdo

                fase_L += omega_L
                if fase_L >= 2.0 * math.pi:
                    fase_L -= 2.0 * math.pi

            data = struct.pack(f"{CHUNK * CHANNELS}f", *samples)
            stream.write(data)

    except KeyboardInterrupt:
        print("\nDeteniendo señal de audio...")
    finally:
        stream.stop_stream()
        stream.close()
        p.terminate()


if __name__ == "__main__":
    main()