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

LEFT_CHANNEL = {   # RECIPIENTE CHICO
     20: (20, 100),
     30: (20,  90),
     40: (15,  70),
     50: (10,  50),
     60: ( 5,  25),
     80: (10,  25),
    100: ( 5,  25),
    150: ( 5,  20),
    250: (15,  20),
    350: (15,  25),
    450: (20,  20),
    550: (30,  30),
}

RIGHT_CHANNEL = {  # RECIPIENTE LARGO
     20: (40, 100),
     30: (20,  85),
     40: (20,  65),
     50: (15,  45),
     60: ( 5,  35),
     80: ( 5,  10),
    100: ( 5,  15),
    150: (10,  20),
    250: (15,  35),
    350: (15,  35),
    450: (20,  30),
    550: (30,  30),
}

# Cuántos segundos dura cada tono antes de elegir uno nuevo
DURACION_TONO = 5.0      # segundos

# ─────────────────────────────────────────────
RATE       = 44100
CHANNELS   = 2
CHUNK      = 1024
# ─────────────────────────────────────────────


def pick_tone(channel_config: dict) -> tuple[float, float]:
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
        freq_L, amp_L = pick_tone(LEFT_CHANNEL)
        freq_R, amp_R = pick_tone(RIGHT_CHANNEL)
        omega_L = 2.0 * math.pi * freq_L / RATE
        omega_R = 2.0 * math.pi * freq_R / RATE
        fase_L = fase_R = 0.0

        ultimo_cambio = time.time()
        print(f"  Izq: {freq_L:.1f} Hz @ {amp_L*100:.1f}%   "
              f"Der: {freq_R:.1f} Hz @ {amp_R*100:.1f}%")

        while True:
            ahora = time.time()

            # ¿Toca elegir nuevas frecuencias?
            if ahora - ultimo_cambio >= DURACION_TONO:
                freq_L, amp_L = pick_tone(LEFT_CHANNEL)
                freq_R, amp_R = pick_tone(RIGHT_CHANNEL)
                omega_L = 2.0 * math.pi * freq_L / RATE
                omega_R = 2.0 * math.pi * freq_R / RATE
                ultimo_cambio = ahora
                print(f"  Izq: {freq_L:.1f} Hz @ {amp_L*100:.1f}%   "
                      f"Der: {freq_R:.1f} Hz @ {amp_R*100:.1f}%")

            # Generar bloque de muestras entrelazadas [L, R, L, R, …]
            samples = []
            for _ in range(CHUNK):
                samples.append(amp_L * math.sin(fase_L))   # canal izquierdo
                samples.append(amp_R * math.sin(fase_R))   # canal derecho

                fase_L += omega_L
                if fase_L >= 2.0 * math.pi:
                    fase_L -= 2.0 * math.pi

                fase_R += omega_R
                if fase_R >= 2.0 * math.pi:
                    fase_R -= 2.0 * math.pi

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