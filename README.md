# Yahtzee con simulación Montecarlo (2 jugadores)

Actividad didáctica 2-M1: simulación del Yahtzee clásico y verificación de la Ley de los Grandes Números.

## Estructura
- `yahtzee.py`: reglas, puntuación, estrategias (Aleatoria, Voraz, Montecarlo) y partida de 2 jugadores.
- `simulacion.py`: experimentos Montecarlo y gráficos (carpeta `resultados/`).
- `resultados/`: CSV y PNG generados.

## Uso
```bash
pip install -r requirements.txt
python yahtzee.py              # una partida narrada: Montecarlo vs Voraz
python simulacion.py           # experimentos (rápido, ~1 min)
python simulacion.py --full    # más réplicas
```

## Metodología USA - MODIFICA - CREA
- **USA**: ejecutar la guía suministrada tal cual y entender el flujo (dados uniformes, turnos, puntuación).
- **MODIFICA**: *(completar con los cambios que hagas sobre la guía)*.
- **CREA**: estrategia Montecarlo que evalúa las 32 combinaciones de dados a conservar por simulación, y experimentos de convergencia (LGN).

## Simplificaciones
- Bonus de 100 por Yahtzee adicional incluido; **no** se aplican reglas de comodín (joker).
- Full house vale 25 solo con trío + par (un Yahtzee no cuenta como full).
- `BASE` (valor esperado por categoría) es una referencia aproximada.

## Resultados (modo rápido, semilla 2024)
| Experimento | Simulado | Teórico/Referencia |
|---|---|---|
| Media de un dado (n=100 000) | 3.4899 | 3.5 |
| P(Yahtzee) en 1 lanzamiento (n=1 000 000) | 0.000793 | 1/1296 = 0.000772 |
| P(Yahtzee) en un turno (n=400 000) | 0.04675 | ≈ 0.046 |
| Puntaje medio Aleatoria / Voraz / Montecarlo | 46.0 / 159.0 / 217.9 | - |
