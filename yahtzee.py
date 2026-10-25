"""
Yahtzee clásico para 2 jugadores simulado con el método de Montecarlo.

Módulo principal: reglas, puntuación, estrategias y partida.
Cada lanzamiento de dado es una variable aleatoria uniforme discreta en {1..6}.
"""
import random
from collections import Counter
from itertools import product

# ----------------------------------------------------------------------------
# 1. REGLAS Y PUNTUACIÓN
# ----------------------------------------------------------------------------
UPPER = ["unos", "doses", "treses", "cuatros", "cincos", "seises"]
LOWER = ["trio", "poker", "full", "escalera_pequena",
         "escalera_grande", "yahtzee", "azar"]
CATEGORIES = UPPER + LOWER

# Valor esperado aproximado de cada categoría (referencia para la heurística
# "puntos obtenidos - puntos que se esperaban obtener"). Se pueden recalcular
# con Montecarlo (ver simulacion.py).
BASE = {"unos": 2.1, "doses": 5.3, "treses": 8.6, "cuatros": 12.2,
        "cincos": 15.7, "seises": 19.2, "trio": 21.7, "poker": 13.1,
        "full": 22.6, "escalera_pequena": 29.5, "escalera_grande": 32.7,
        "yahtzee": 16.9, "azar": 22.0}


def puntaje(cat, dados):
    """Puntos que daría `dados` si se anota en la categoría `cat`."""
    c = Counter(dados)
    total = sum(dados)
    if cat in UPPER:
        cara = UPPER.index(cat) + 1
        return cara * c[cara]
    if cat == "trio":
        return total if max(c.values()) >= 3 else 0
    if cat == "poker":
        return total if max(c.values()) >= 4 else 0
    if cat == "full":
        return 25 if sorted(c.values()) == [2, 3] else 0
    caras = set(dados)
    if cat == "escalera_pequena":
        return 30 if any({a, a + 1, a + 2, a + 3} <= caras for a in (1, 2, 3)) else 0
    if cat == "escalera_grande":
        return 40 if caras in ({1, 2, 3, 4, 5}, {2, 3, 4, 5, 6}) else 0
    if cat == "yahtzee":
        return 50 if max(c.values()) == 5 else 0
    if cat == "azar":
        return total
    raise ValueError(cat)


def es_yahtzee(dados):
    return len(set(dados)) == 1


# ----------------------------------------------------------------------------
# 2. ESTRATEGIAS (cada una decide qué dados conservar y dónde anotar)
# ----------------------------------------------------------------------------
class Aleatoria:
    """Línea base: conserva dados al azar y anota en una categoría al azar."""
    nombre = "Aleatoria"

    def __init__(self, rng): self.rng = rng

    def conservar(self, dados, libres):
        return [self.rng.random() < 0.5 for _ in dados]

    def categoria(self, dados, libres):
        return self.rng.choice(libres)


class Voraz:
    """Conserva la cara más repetida y anota donde obtiene más puntos."""
    nombre = "Voraz"

    def __init__(self, rng): self.rng = rng

    def conservar(self, dados, libres):
        c = Counter(dados)
        cara = max(c, key=lambda k: (c[k], k))
        return [d == cara for d in dados]

    def categoria(self, dados, libres):
        # en empate, sacrifica la categoría de menor valor esperado
        return max(libres, key=lambda k: (puntaje(k, dados), -BASE[k]))


class Montecarlo:
    """
    Para cada una de las 32 combinaciones de dados a conservar, simula
    `n_sim` relanzamientos y elige la que maximiza el valor medio
    (puntos - BASE) de la mejor categoría libre. Es decir, decide por
    esperanza matemática estimada, no por una regla fija.
    """
    nombre = "Montecarlo"

    def __init__(self, rng, n_sim=30):
        self.rng, self.n_sim = rng, n_sim

    def _valor(self, dados, libres):
        return max(puntaje(c, dados) - BASE[c] for c in libres)

    def conservar(self, dados, libres):
        mejor, mejor_v = None, float("-inf")
        for mascara in product([True, False], repeat=5):
            if all(mascara):
                v = self._valor(dados, libres)
            else:
                tot = 0.0
                for _ in range(self.n_sim):
                    nuevo = [d if k else self.rng.randint(1, 6)
                             for d, k in zip(dados, mascara)]
                    tot += self._valor(nuevo, libres)
                v = tot / self.n_sim
            if v > mejor_v:
                mejor, mejor_v = list(mascara), v
        return mejor

    def categoria(self, dados, libres):
        return max(libres, key=lambda k: puntaje(k, dados) - BASE[k])


# ----------------------------------------------------------------------------
# 3. TURNO Y PARTIDA
# ----------------------------------------------------------------------------
class Jugador:
    def __init__(self, nombre, estrategia):
        self.nombre, self.estrategia = nombre, estrategia
        self.hoja = {}          # categoría -> puntos
        self.bonus_yahtzee = 0

    @property
    def libres(self):
        return [c for c in CATEGORIES if c not in self.hoja]

    def subtotal_superior(self):
        return sum(self.hoja.get(c, 0) for c in UPPER)

    def bonus_superior(self):
        return 35 if self.subtotal_superior() >= 63 else 0

    def total(self):
        return sum(self.hoja.values()) + self.bonus_superior() + self.bonus_yahtzee


def jugar_turno(jugador, rng, verbose=False):
    """Hasta 3 lanzamientos de 5 dados; devuelve (dados finales, hubo_yahtzee)."""
    dados = [rng.randint(1, 6) for _ in range(5)]
    for lanzamiento in (1, 2):
        if verbose:
            print(f"   lanzamiento {lanzamiento}: {sorted(dados)}")
        mascara = jugador.estrategia.conservar(dados, jugador.libres)
        if all(mascara):
            break
        dados = [d if k else rng.randint(1, 6) for d, k in zip(dados, mascara)]
    else:
        if verbose:
            print(f"   lanzamiento 3: {sorted(dados)}")
    cat = jugador.estrategia.categoria(dados, jugador.libres)
    pts = puntaje(cat, dados)
    # bonus por Yahtzee adicional (sin reglas de comodín)
    if es_yahtzee(dados) and jugador.hoja.get("yahtzee") == 50:
        jugador.bonus_yahtzee += 100
    jugador.hoja[cat] = pts
    if verbose:
        print(f"   -> anota {pts} en '{cat}'")
    return dados, es_yahtzee(dados)


def jugar_partida(estrategias, rng=None, verbose=False):
    """Partida de 13 rondas entre 2 jugadores. Devuelve la lista de jugadores."""
    rng = rng or random.Random()
    jugadores = [Jugador(f"J{i + 1} ({e.nombre})", e)
                 for i, e in enumerate(estrategias)]
    for ronda in range(1, 14):
        for j in jugadores:
            if verbose:
                print(f"Ronda {ronda} - {j.nombre}")
            jugar_turno(j, rng, verbose)
    if verbose:
        print("\n=== RESULTADO FINAL ===")
        for j in jugadores:
            print(f"{j.nombre}: {j.total()} puntos "
                  f"(bonus superior {j.bonus_superior()}, bonus yahtzee {j.bonus_yahtzee})")
        a, b = jugadores
        if a.total() == b.total():
            print("Empate")
        else:
            print("Gana", (a if a.total() > b.total() else b).nombre)
    return jugadores


if __name__ == "__main__":
    rng = random.Random(42)
    jugar_partida([Montecarlo(rng), Voraz(rng)], rng, verbose=True)
