#!/usr/bin/env python3
"""
Simulación de recolección de datos de humedad del suelo.

- M = 3 sensores, N = 144 lecturas por sensor, intervalo de 5 min (12 h en total).
- Rango válido: 20 % a 90 %.
- Cada sensor tiene un patrón propio (ciclo + tendencia + ruido).
- El sensor 3 es "defectuoso": mucho más ruido, drift y fallas (valor congelado).
- Se inyectan rachas fuera de rango en posiciones conocidas (en sensores distintos).
- Salida: humedad.csv con columnas sensor, nro, valor.
"""

import csv
import math
import random

# --------------------------- Parámetros ---------------------------
M = 3                 # cantidad de sensores
N = 144               # lecturas por sensor
INTERVALO_MIN = 5     # minutos entre lecturas
VMIN, VMAX = 20.0, 90.0
SEMILLA = 42
ARCHIVO = "humedad.csv"

# Rachas fuera de rango inyectadas: (sensor, nro_inicio, nro_fin, tipo)
#   "alto" -> valores > 90 ; "bajo" -> valores < 20
RACHAS = [
    (1, 40, 47, "alto"),     # sensor 1: 8 lecturas por encima de 90
    (2, 100, 106, "bajo"),   # sensor 2: 7 lecturas por debajo de 20
    (3, 120, 124, "alto"),   # sensor 3: 5 lecturas por encima de 90
]

random.seed(SEMILLA)


def generar_sensor(s: int) -> list[float]:
    """Genera N lecturas 'limpias' (dentro de 20-90) con un patrón por sensor."""
    valores = []
    periodo = 24 * 60 / INTERVALO_MIN          # lecturas por ciclo diario (288)
    congelado_hasta, valor_congelado = -1, None  # para fallas del sensor 3

    for i in range(N):
        fase = 2 * math.pi * i / periodo

        if s == 1:
            # Suelo bien regulado: ciclo diario suave + ruido bajo
            v = 60 + 6 * math.sin(fase) + random.gauss(0, 0.6)

        elif s == 2:
            # Suelo que se seca: tendencia descendente + pequeño ciclo + ruido medio
            v = 72 - 0.15 * i + 2.5 * math.sin(fase + 1.0) + random.gauss(0, 1.0)
            # Riego a mitad del período: salto de humedad que luego decae
            if i >= 80:
                v += 18 * math.exp(-(i - 80) / 25)

        else:
            # Sensor defectuoso: ciclo + drift creciente + ruido alto + fallas
            v = 50 + 5 * math.sin(fase + 2.0) + 0.08 * i + random.gauss(0, 3.5)
            # Fallas: el sensor se "congela" repitiendo el último valor
            if i >= congelado_hasta and random.random() < 0.02:
                congelado_hasta = i + random.randint(4, 9)
                valor_congelado = valores[-1] if valores else v
            if i < congelado_hasta:
                v = valor_congelado

        # Los datos "normales" siempre quedan dentro del rango válido
        valores.append(round(min(VMAX - 0.5, max(VMIN + 0.5, v)), 2))

    return valores


def inyectar_rachas(datos: dict[int, list[float]]) -> None:
    """Reemplaza tramos por valores fuera de rango en posiciones conocidas."""
    for sensor, ini, fin, tipo in RACHAS:
        for nro in range(ini, fin + 1):
            if tipo == "alto":
                datos[sensor][nro - 1] = round(random.uniform(91, 100), 2)
            else:
                datos[sensor][nro - 1] = round(random.uniform(0, 19), 2)


def main() -> None:
    datos = {s: generar_sensor(s) for s in range(1, M + 1)}
    inyectar_rachas(datos)

    with open(ARCHIVO, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["sensor", "nro", "valor"])
        for s in range(1, M + 1):
            for nro, v in enumerate(datos[s], start=1):
                w.writerow([s, nro, v])

    print(f"Archivo '{ARCHIVO}' generado: {M * N} filas.")
    print("Rachas fuera de rango inyectadas (verdad conocida):")
    for sensor, ini, fin, tipo in RACHAS:
        print(f"  sensor {sensor}: nro {ini}-{fin} ({tipo})")


if __name__ == "__main__":
    main()
