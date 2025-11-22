# Ranges por Categoría (Basado en Percentiles)

Metodología: Para cada columna numérica se calcularon los percentiles 10 (P10), 25 (P25), 50 (P50), 75 (P75) y 90 (P90). Estos se usan como puntos de corte para definir los límites de cada categoría:

```
Extremely_Low   ≤ P10
Low             > P10 y ≤ P25
Moderate        > P25 y ≤ P50
High            > P50 y ≤ P75
Extremely_High  > P75 (referencia P90 como valor típico alto)
```

Nota: Para cada variable solo se listan los valores de los percentiles como referencia. Dependiendo de si «más alto» o «más bajo» es deseable, el consumidor de este archivo puede invertir la lógica. Ejemplos: ruido, crimen ⇒ se prefiere bajo; ingresos, equipamientos ⇒ se prefiere alto.

---

## median_household_income
Extremely_Low: 51100.00
Low: 61438.50
Moderate: 93521.00
High: 120937.50
Extremely_High: 168972.20 (≥ High)

## surface_area
Extremely_Low: 1.00
Low: 2.00
Moderate: 3.00
High: 5.98
Extremely_High: 8.00

## population_density
Extremely_Low: 297.15
Low: 534.25
Moderate: 976.88
High: 2012.25
Extremely_High: 3463.90

## average_age
Extremely_Low: 31.73
Low: 35.05
Moderate: 38.95
High: 43.55
Extremely_High: 47.95

## families_with_children_percentage
Extremely_Low: 17.74
Low: 29.24
Moderate: 38.04
High: 55.23
Extremely_High: 69.35

## rent_vs_own_percentage
Extremely_Low: 14.03
Low: 35.32
Moderate: 55.38
High: 74.48
Extremely_High: 87.67

## unemployment_rate
Extremely_Low: 3.40
Low: 5.75
Moderate: 7.90
High: 9.75
Extremely_High: 13.10

## education_level_percentage
Extremely_Low: 9.20
Low: 19.55
Moderate: 37.10
High: 62.75
Extremely_High: 73.20

## total_crimes
Extremely_Low: 2134.30
Low: 3908.00
Moderate: 6989.00
High: 11782.25
Extremely_High: 15244.70

## violent_ratio
Extremely_Low: 0.1630
Low: 0.1912
Moderate: 0.2569
High: 0.3193
Extremely_High: 0.3825

## property_ratio
Extremely_Low: 0.5472
Low: 0.6186
Moderate: 0.6710
High: 0.7465
Extremely_High: 0.7908

## violent_vs_property_ratio
Extremely_Low: 0.2061
Low: 0.2553
Moderate: 0.3890
High: 0.5137
Extremely_High: 0.7007

## crime_trend_slope
Extremely_Low: -10.94
Low: -6.79
Moderate: -4.39
High: -2.31
Extremely_High: -1.39 (menos negativo)

## crimes_per_100_people
Extremely_Low: 75.30
Low: 112.64
Moderate: 219.85
High: 373.91
Extremely_High: 545.89

## median_rent
Extremely_Low: 1324.30
Low: 1517.50
Moderate: 1867.00
High: 2398.50
Extremely_High: 3268.00

## median_home_price
Extremely_Low: 558840.00
Low: 667000.00
Moderate: 940800.00
High: 1506000.00
Extremely_High: 2000000.00

## average_housing_age
Extremely_Low: 45.00
Low: 52.00
Moderate: 63.00
High: 71.50
Extremely_High: 78.00

## average_dB_level
Extremely_Low: 50.00
Low: 60.00
Moderate: 60.00
High: 65.00
Extremely_High: 65.00

## maximum_dB_level
Extremely_Low: 70.00
Low: 80.00
Moderate: 80.00
High: 85.00
Extremely_High: 90.00

## gym_density
Extremely_Low: 0.30
Low: 0.50
Moderate: 1.00
High: 1.83
Extremely_High: 2.50

## culture_density
Extremely_Low: 0.00
Low: 0.21
Moderate: 0.50
High: 1.10
Extremely_High: 2.00

## local_businesses_density
Extremely_Low: 1.27
Low: 2.38
Moderate: 5.00
High: 11.81
Extremely_High: 18.00

## restaurant_density
Extremely_Low: 2.50
Low: 4.36
Moderate: 8.17
High: 16.88
Extremely_High: 27.60

## premium_stores_density
Extremely_Low: 0.00
Low: 0.00
Moderate: 0.00
High: 0.83
Extremely_High: 2.74

## nightlife_density
Extremely_Low: 0.39
Low: 1.00
Moderate: 1.78
High: 5.00
Extremely_High: 8.26

## hospital_density
Extremely_Low: 0.20
Low: 0.39
Moderate: 0.81
High: 1.13
Extremely_High: 2.00

## dist_downtown_km
Extremely_Low: 5.09
Low: 7.59
Moderate: 13.02
High: 23.44
Extremely_High: 31.78

## proximity_to_sea
Extremely_Low: 7.40
Low: 13.90
Moderate: 18.46
High: 24.20
Extremely_High: 29.21

## green_space_percentage
Extremely_Low: 6.60
Low: 10.00
Moderate: 18.00
High: 30.00
Extremely_High: 53.50

## charging_stations_number
Extremely_Low: 15.00
Low: 25.00
Moderate: 35.00
High: 48.75
Extremely_High: 60.00

## walk_score
Extremely_Low: 44.30
Low: 55.00
Moderate: 69.00
High: 76.75
Extremely_High: 85.00

## transit_score
Extremely_Low: 31.50
Low: 44.00
Moderate: 50.00
High: 60.00
Extremely_High: 70.00

## bike_score
Extremely_Low: 39.30
Low: 50.00
Moderate: 57.00
High: 65.00
Extremely_High: 70.70

## accessibility_score
Extremely_Low: 50.00
Low: 60.00
Moderate: 65.00
High: 75.00
Extremely_High: 85.00