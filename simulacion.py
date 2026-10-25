"""
Experimentos Montecarlo sobre Yahtzee y verificación de la Ley de los Grandes Números.

Uso:  python simulacion.py            (rápido)
      python simulacion.py --full     (más réplicas, más preciso)
"""
import csv
import random
import statistics as st
import sys
import time

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

from yahtzee import (Aleatoria, Voraz, Montecarlo, jugar_partida, es_yahtzee,
                     CATEGORIES, Jugador, jugar_turno)

FULL = "--full" in sys.argv
SEED = 2024
OUT = "resultados"


def guardar(nombre, filas, cabecera):
    with open(f"{OUT}/{nombre}.csv", "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(cabecera)
        w.writerows(filas)


def trayectoria(n, muestra, paso):
    """Promedio acumulado de la secuencia muestra() en puntos n/paso."""
    acum, xs, ys = 0.0, [], []
    for i in range(1, n + 1):
        acum += muestra()
        if i % paso == 0 or i == 1:
            xs.append(i)
            ys.append(acum / i)
    return xs, ys


# ---------------------------------------------------------------------------
# Exp. 1: media de un dado -> 3.5
# ---------------------------------------------------------------------------
def exp_dado(rng):
    n = 200_000 if FULL else 100_000
    xs, ys = trayectoria(n, lambda: rng.randint(1, 6), n // 400)
    guardar("exp1_dado", zip(xs, ys), ["n", "media"])
    plt.figure(figsize=(8, 4))
    plt.semilogx(xs, ys, label="media muestral")
    plt.axhline(3.5, color="r", ls="--", label="E[X] = 3.5")
    plt.xlabel("Número de lanzamientos n"); plt.ylabel("Media acumulada")
    plt.title("LGN: media de un dado"); plt.legend(); plt.tight_layout()
    plt.savefig(f"{OUT}/exp1_dado.png", dpi=130); plt.close()
    print(f"[Exp1] media tras {n} lanzamientos: {ys[-1]:.4f} (teórico 3.5)")


# ---------------------------------------------------------------------------
# Exp. 2: P(Yahtzee en un solo lanzamiento) = 6/6^5 = 1/1296
# ---------------------------------------------------------------------------
def exp_yahtzee_un_lanzamiento(rng):
    n = 3_000_000 if FULL else 1_000_000
    p_teo = 1 / 1296
    xs, ys, aciertos = [], [], 0
    paso = n // 400
    for i in range(1, n + 1):
        d = [rng.randint(1, 6) for _ in range(5)]
        aciertos += es_yahtzee(d)
        if i % paso == 0:
            xs.append(i); ys.append(aciertos / i)
    guardar("exp2_yahtzee_1_lanzamiento", zip(xs, ys), ["n", "frecuencia"])
    plt.figure(figsize=(8, 4))
    plt.semilogx(xs, ys, label="frecuencia relativa")
    plt.axhline(p_teo, color="r", ls="--", label=f"teórica = 1/1296 = {p_teo:.5f}")
    plt.xlabel("Número de lanzamientos n"); plt.ylabel("Frecuencia de Yahtzee")
    plt.title("LGN: Yahtzee en un solo lanzamiento de 5 dados")
    plt.legend(); plt.tight_layout()
    plt.savefig(f"{OUT}/exp2_yahtzee_1_lanzamiento.png", dpi=130); plt.close()
    print(f"[Exp2] frecuencia tras {n}: {ys[-1]:.6f} (teórico {p_teo:.6f})")


# ---------------------------------------------------------------------------
# Exp. 3: P(Yahtzee en un turno de 3 lanzamientos) con estrategia "conservar
# la cara más repetida". Valor de referencia conocido ≈ 0.0460
# ---------------------------------------------------------------------------
def turno_yahtzee(rng):
    from collections import Counter
    d = [rng.randint(1, 6) for _ in range(5)]
    for _ in range(2):
        c = Counter(d)
        cara = max(c, key=lambda k: (c[k], k))
        d = [x if x == cara else rng.randint(1, 6) for x in d]
    return es_yahtzee(d)


def exp_yahtzee_turno(rng):
    n = 1_000_000 if FULL else 400_000
    xs, ys, aciertos = [], [], 0
    paso = n // 400
    for i in range(1, n + 1):
        aciertos += turno_yahtzee(rng)
        if i % paso == 0:
            xs.append(i); ys.append(aciertos / i)
    guardar("exp3_yahtzee_turno", zip(xs, ys), ["n", "frecuencia"])
    plt.figure(figsize=(8, 4))
    plt.semilogx(xs, ys, label="frecuencia relativa")
    plt.axhline(0.046, color="r", ls="--", label="valor de referencia ≈ 0.046")
    plt.xlabel("Número de turnos n"); plt.ylabel("P(Yahtzee en el turno)")
    plt.title("LGN: Yahtzee en un turno (3 lanzamientos)")
    plt.legend(); plt.tight_layout()
    plt.savefig(f"{OUT}/exp3_yahtzee_turno.png", dpi=130); plt.close()
    print(f"[Exp3] frecuencia tras {n} turnos: {ys[-1]:.5f} (referencia ~0.046)")


# ---------------------------------------------------------------------------
# Exp. 4: comparación de estrategias (puntaje medio por partida)
# ---------------------------------------------------------------------------
def media_estrategia(clase, n, rng, **kw):
    pts = []
    for _ in range(n):
        j = jugar_partida([clase(rng, **kw), Voraz(rng)], rng)[0]
        pts.append(j.total())
    return pts


def exp_estrategias(rng):
    n_simple = 20_000 if FULL else 5_000
    n_mc = 600 if FULL else 150
    t = time.time()
    res = {
        "Aleatoria": media_estrategia(Aleatoria, n_simple, rng),
        "Voraz": media_estrategia(Voraz, n_simple, rng),
        "Montecarlo": media_estrategia(Montecarlo, n_mc, rng, n_sim=25),
    }
    filas = []
    print("[Exp4] puntaje medio por partida (J1 vs Voraz):")
    for k, v in res.items():
        m, s = st.mean(v), st.stdev(v)
        ee = s / len(v) ** 0.5
        filas.append([k, len(v), round(m, 2), round(s, 2), round(1.96 * ee, 2)])
        print(f"   {k:11s} n={len(v):6d}  media={m:7.2f}  desv={s:6.2f}  IC95%=±{1.96*ee:.2f}")
    guardar("exp4_estrategias", filas, ["estrategia", "n", "media", "desv", "IC95"])
    plt.figure(figsize=(6, 4))
    plt.bar([f[0] for f in filas], [f[2] for f in filas],
            yerr=[f[4] for f in filas], capsize=6, color=["#999", "#4a8", "#37c"])
    plt.ylabel("Puntaje medio"); plt.title("Estrategias en Yahtzee (IC 95%)")
    plt.tight_layout(); plt.savefig(f"{OUT}/exp4_estrategias.png", dpi=130); plt.close()
    print(f"   (tiempo {time.time() - t:.0f}s)")
    return res


# ---------------------------------------------------------------------------
# Exp. 5: convergencia del puntaje medio de la estrategia Voraz
# ---------------------------------------------------------------------------
def exp_convergencia_puntaje(rng):
    n = 20_000 if FULL else 6_000
    xs, ys = trayectoria(
        n, lambda: jugar_partida([Voraz(rng), Voraz(rng)], rng)[0].total(), n // 200)
    guardar("exp5_convergencia_puntaje", zip(xs, ys), ["n_partidas", "media"])
    plt.figure(figsize=(8, 4))
    plt.semilogx(xs, ys, label="puntaje medio acumulado")
    plt.axhline(ys[-1], color="r", ls="--", label=f"estimación final {ys[-1]:.1f}")
    plt.xlabel("Número de partidas n"); plt.ylabel("Puntaje medio")
    plt.title("LGN: puntaje medio de la estrategia Voraz")
    plt.legend(); plt.tight_layout()
    plt.savefig(f"{OUT}/exp5_convergencia_puntaje.png", dpi=130); plt.close()
    print(f"[Exp5] puntaje medio estimado (Voraz): {ys[-1]:.2f}")


if __name__ == "__main__":
    rng = random.Random(SEED)
    exp_dado(rng)
    exp_yahtzee_un_lanzamiento(rng)
    exp_yahtzee_turno(rng)
    exp_convergencia_puntaje(rng)
    exp_estrategias(rng)
    print("Listo. Resultados en la carpeta 'resultados/'")
