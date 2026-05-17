import math
import time
import random
import struct
import pyaudio

# ─────────────────────────────────────────────
#  CONFIGURACIÓN  ── edita aquí
# ─────────────────────────────────────────────
#
#  Formato: { frecuencia_hz: (vol_min_%, vol_max_%) }
#  Frecuencias con (0, 0) nunca sonarán.

CHANNEL = {   # RECIPIENTE GRANDE
     20: (10, 50),
     30: (10, 60),
     40: ( 5, 25),
     50: (10, 45),
     60: ( 0,  0),
     80: ( 0,  0),
    100: ( 0,  0),
    150: ( 0,  0),
    250: ( 0,  0),
    350: ( 0,  0),
    450: ( 0,  0),
    550: ( 0,  0),
}

# Cuántos segundos dura cada tono antes de elegir uno nuevo
DURACION_TONO = 5.0

IZQ = "IZQUIERDA"
DER = "DERECHA"
LADO = IZQ   # "IZQUIERDA" o "DERECHA"

# ─────────────────────────────────────────────
RATE     = 44100
CHANNELS = 2
CHUNK    = 1024
# ─────────────────────────────────────────────

ACTIVE = {f: r for f, r in CHANNEL.items() if r != (0, 0)}


def pick_tone(config: dict) -> tuple:
    """Devuelve (frecuencia, amplitud) aleatorios del canal dado."""
    freq = random.choice(list(config.keys()))
    vol_min, vol_max = config[freq]
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

    lado_nombre = LADO.capitalize()
    print(f"Iniciando generador — Recipiente Grande — canal {lado_nombre}.")
    print(f"Cada {DURACION_TONO} s se elige una nueva frecuencia.\n")

    izquierda = LADO.upper() == "IZQUIERDA"

    try:
        freq, amp = pick_tone(ACTIVE)
        omega = 2.0 * math.pi * freq / RATE
        fase  = 0.0
        ultimo_cambio = time.time()
        print(f"  {freq:.1f} Hz @ {amp*100:.1f}%")

        while True:
            ahora = time.time()

            if ahora - ultimo_cambio >= DURACION_TONO:
                freq, amp = pick_tone(ACTIVE)
                omega = 2.0 * math.pi * freq / RATE
                ultimo_cambio = ahora
                print(f"  {freq:.1f} Hz @ {amp*100:.1f}%")

            samples = []
            for _ in range(CHUNK):
                s = amp * math.sin(fase)
                if izquierda:
                    samples.append(s)    # izquierda
                    samples.append(0.0)  # derecha en silencio
                else:
                    samples.append(0.0)  # izquierda en silencio
                    samples.append(s)    # derecha
                fase += omega
                if fase >= 2.0 * math.pi:
                    fase -= 2.0 * math.pi

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