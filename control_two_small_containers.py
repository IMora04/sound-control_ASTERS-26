import math
import time
import random
import struct
import datetime
import pyaudio

# ─────────────────────────────────────────────
#  CONFIGURACIÓN
# ─────────────────────────────────────────────
LEFT_CHANNEL = {
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

RIGHT_CHANNEL = {
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

# ─────────────────────────────────────────────
RATE     = 44100
CHANNELS = 2
CHUNK    = 1024

indices       = [1, 2, 3, 4, 5]
indices_local = [1, 2]             # ← cambiar según Raspberry

CONFIGS_LOCALES = {
    1: LEFT_CHANNEL,
    2: RIGHT_CHANNEL,
}

dia_del_año = datetime.datetime.now().timetuple().tm_yday
rng = random.Random(dia_del_año)

# ─────────────────────────────────────────────
#  PERMS
# ─────────────────────────────────────────────
def get_next_perm(previous_perm_index):
    perm_ids = indices[:]
    rng.shuffle(perm_ids)
    new_perm = {}
    for i in indices:
        position   = perm_ids.index(i)
        predecesor = perm_ids[(position - 1) % len(indices)]
        new_perm[i] = PERMS[previous_perm_index][predecesor]
    print(f"  [ronda {previous_perm_index + 1} calculada] "
          f"perm: {perm_ids} → valores: {new_perm}")
    return new_perm

def limpiar_perms():
    """Elimina las perms que ningún ID necesitará ya."""
    minima = min(ESTADO[id_]["perm"] for id_ in indices)
    to_delete = [k for k in PERMS if k < minima]
    for k in to_delete:
        del PERMS[k]
        print(f"  [ronda {k} eliminada]")

PERMS = {
    0: {1: 17, 2: 23, 3: 31, 4: 41, 5: 53},
}
PERMS[1] = get_next_perm(0)

# ─────────────────────────────────────────────
#  ESTADO
# ─────────────────────────────────────────────
ESTADO = {
    id_: {"perm": 0, "tiempo_inicio": time.time()}
    for id_ in indices
}

def get_duracion(id_):
    perm_index      = ESTADO[id_]["perm"]
    duracion        = PERMS[perm_index][id_]
    ESTADO[id_]["perm"] += 1

    siguiente = ESTADO[id_]["perm"] + 1
    if siguiente not in PERMS:
        PERMS[siguiente] = get_next_perm(siguiente - 1)

    limpiar_perms()

    return duracion

def actualizar_remotos():
    ahora = time.time()
    for id_ in indices:
        if id_ in indices_local:
            continue
        while ahora - ESTADO[id_]["tiempo_inicio"] >= PERMS[ESTADO[id_]["perm"]][id_]:
            dur = get_duracion(id_)
            ESTADO[id_]["tiempo_inicio"] += dur
            print(f"  [remoto {id_}] → nueva duración {PERMS[ESTADO[id_]['perm']][id_]}s")

# ─────────────────────────────────────────────
#  AUDIO
# ─────────────────────────────────────────────
def pick_tone(channel_config: dict) -> tuple:
    freq = rng.choice(list(channel_config.keys()))
    vol_min, vol_max = channel_config[freq]
    pct = rng.uniform(vol_min, vol_max)
    amp = max(0.0, min(1.0, pct / 100.0))
    return float(freq), amp

class Canal:
    def __init__(self, id_: int, config: dict):
        self.id_      = id_
        self.config   = config
        self.duracion = get_duracion(self.id_)

        self.freq, self.amp = pick_tone(self.config)
        self.omega = 2.0 * math.pi * self.freq / RATE
        self.fase  = 0.0
        self.ultimo_cambio = time.time()
        ESTADO[self.id_]["tiempo_inicio"] = self.ultimo_cambio

        print(f"  [recipiente {self.id_}] {self.freq:.1f} Hz "
              f"@ {self.amp*100:.1f}% durante {self.duracion}s")

    def actualizar(self):
        ahora = time.time()
        if ahora - self.ultimo_cambio >= self.duracion:
            self.duracion = get_duracion(self.id_)
            ESTADO[self.id_]["tiempo_inicio"] = ahora
            self.ultimo_cambio = ahora
            self.freq, self.amp = pick_tone(self.config)
            self.omega = 2.0 * math.pi * self.freq / RATE
            print(f"  [recipiente {self.id_}] {self.freq:.1f} Hz "
                  f"@ {self.amp*100:.1f}% durante {self.duracion}s")

    def muestra(self) -> float:
        s = self.amp * math.sin(self.fase)
        self.fase += self.omega
        if self.fase >= 2.0 * math.pi:
            self.fase -= 2.0 * math.pi
        return s

def main():
    print(f"Día del año: {dia_del_año} → semilla: {dia_del_año}")
    print(f"Índices locales: {indices_local}\n")
    print(f"  [ronda 0] valores: {PERMS[0]}")

    canales = [
        Canal(id_, CONFIGS_LOCALES[id_])
        for id_ in indices_local
    ]

    p = pyaudio.PyAudio()
    stream = p.open(
        format=pyaudio.paFloat32,
        channels=CHANNELS,
        rate=RATE,
        output=True,
    )

    try:
        while True:
            actualizar_remotos()

            for canal in canales:
                canal.actualizar()

            samples = []
            for _ in range(CHUNK):
                if len(canales) == 2:
                    samples.append(canales[0].muestra())
                    samples.append(canales[1].muestra())
                else:
                    s = canales[0].muestra()
                    samples.append(s)
                    samples.append(s)

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