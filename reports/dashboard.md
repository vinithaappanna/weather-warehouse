# Weather Warehouse - daily dashboard

Generated 2026-11-28 12:09 UTC.

| city | day | avg_temp_c | min_temp_c | max_temp_c | total_precip_mm | max_wind_kmh | hours_observed |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Chicago | 2026-11-28 | 4.58 | 0.7 | 9.2 | 0.0 | 19.4 | 24 |
| New York | 2026-11-28 | 6.79 | 4.9 | 9.0 | 0.0 | 24.5 | 24 |
| Newark | 2026-11-28 | 6.49 | 4.0 | 9.2 | 0.0 | 22.1 | 24 |
| San Francisco | 2026-11-28 | 13.04 | 10.9 | 16.5 | 0.0 | 14.1 | 24 |
| Chicago | 2026-11-27 | 4.21 | 1.8 | 6.8 | 9.7 | 36.7 | 24 |
| New York | 2026-11-27 | 10.55 | 6.4 | 13.9 | 0.4 | 26.8 | 24 |
| Newark | 2026-11-27 | 10.16 | 6.4 | 12.6 | 0.0 | 21.7 | 24 |
| San Francisco | 2026-11-27 | 12.19 | 9.2 | 15.9 | 0.0 | 11.9 | 24 |
| Chicago | 2026-11-26 | 5.6 | 4.1 | 6.6 | 12.7 | 36.7 | 24 |
| New York | 2026-11-26 | 7.02 | 5.6 | 10.9 | 40.8 | 42.0 | 24 |
| Newark | 2026-11-26 | 6.31 | 4.6 | 10.8 | 43.5 | 40.0 | 24 |
| San Francisco | 2026-11-26 | 12.55 | 10.1 | 16.4 | 0.0 | 10.4 | 24 |
| Chicago | 2026-11-25 | 3.34 | 0.7 | 5.4 | 0.0 | 29.0 | 24 |
| New York | 2026-11-25 | 3.47 | -0.1 | 5.9 | 0.0 | 18.1 | 24 |
| Newark | 2026-11-25 | 3.49 | -0.3 | 6.9 | 0.0 | 19.4 | 24 |
| San Francisco | 2026-11-25 | 13.15 | 10.6 | 15.9 | 3.3 | 11.4 | 24 |
| Chicago | 2026-11-24 | 1.35 | -1.8 | 4.5 | 0.0 | 18.8 | 24 |
| New York | 2026-11-24 | 6.8 | 2.1 | 10.0 | 0.0 | 23.5 | 24 |
| Newark | 2026-11-24 | 7.12 | 2.6 | 10.1 | 0.0 | 24.6 | 24 |
| San Francisco | 2026-11-24 | 11.52 | 7.9 | 14.9 | 5.0 | 10.4 | 24 |
| Chicago | 2026-11-23 | 1.32 | -1.1 | 5.5 | 0.0 | 16.6 | 24 |
| New York | 2026-11-23 | 15.39 | 10.2 | 20.9 | 0.0 | 20.6 | 24 |
| Newark | 2026-11-23 | 15.54 | 10.5 | 21.5 | 0.0 | 20.2 | 24 |
| San Francisco | 2026-11-23 | 9.25 | 5.5 | 13.0 | 0.0 | 10.8 | 24 |
| Chicago | 2026-11-22 | 9.15 | 2.7 | 13.3 | 1.8 | 20.0 | 24 |
| New York | 2026-11-22 | 13.73 | 12.2 | 15.4 | 0.0 | 12.9 | 24 |
| Newark | 2026-11-22 | 13.4 | 11.3 | 15.5 | 0.0 | 11.5 | 24 |
| San Francisco | 2026-11-22 | 10.14 | 7.7 | 12.1 | 0.0 | 11.1 | 24 |
| Chicago | 2026-11-21 | 12.69 | 7.2 | 20.1 | 0.0 | 15.8 | 24 |
| New York | 2026-11-21 | 12.79 | 8.1 | 19.0 | 0.0 | 10.5 | 24 |

## Heat / cold exposure (current window)

Hours at or above 30C / at or below 0C and degree-hours beyond each threshold. Illustrative thresholds, not clinical guidance.

| city | heat hours | cold hours | heat degree-hours | cold degree-hours |
| --- | ---: | ---: | ---: | ---: |
| Chicago | 0 | 19 | 0.0 | 20.3 |
| New York | 0 | 3 | 0.0 | 0.2 |
| Newark | 0 | 3 | 0.0 | 0.8 |
| San Francisco | 0 | 0 | 0.0 | 0.0 |

## Unusual days

Completed days only: daily average temperature vs the city's other days (|z| >= 2). Informational: weather, not a data-quality failure.

| city | day | avg temp C | z-score |
| --- | --- | ---: | ---: |
| Chicago | 2026-11-21 | 12.69 | 2.18 |
| New York | 2026-11-25 | 3.47 | -2.1 |
| Newark | 2026-11-25 | 3.49 | -2.07 |
| Newark | 2026-11-23 | 15.54 | 2.01 |

## Precipitation

Model output in mm over the window; the current day includes forecast hours.

![Daily precipitation by city](precip_by_city.png)

| city | total mm | wet days (>=1 mm) |
| --- | ---: | ---: |
| San Francisco | 104.1 | 10 |
| Newark | 78.2 | 3 |
| New York | 66.5 | 3 |
| Chicago | 40.9 | 7 |

## City leaders, 2026-11-27 (latest day complete in every city)

Model output, not station readings.

- Warmest high: San Francisco (15.9 C)
- Coldest low: Chicago (1.8 C)
- Wettest: Chicago (9.7 mm)
- Windiest: Chicago (36.7 km/h)

## Source freshness

Last successful Open-Meteo fetch per city (empty or failed fetches do not count). The latest hour is normally ahead of now because the feed includes forecast hours.

| City | Last successful fetch | Age (h) | Failed fetches since | Latest hour held |
| --- | --- | ---: | ---: | --- |
| Chicago | 2026-11-28 07:08:59.780364 | 0.0 | 0 | 2026-11-28 23:00:00 |
| New York | 2026-11-28 07:08:59.780364 | 0.0 | 0 | 2026-11-28 23:00:00 |
| Newark | 2026-11-28 07:08:59.780364 | 0.0 | 0 | 2026-11-28 23:00:00 |
| San Francisco | 2026-11-28 07:08:59.780364 | 0.0 | 0 | 2026-11-28 23:00:00 |

## Dry-day streaks (rain under 1 mm)

Consecutive completed days below 1 mm of rain. Model output; illustrative, not a drought measure.

| City | Current streak (days) | Longest streak (days) |
| --- | ---: | ---: |
| Chicago | 0 | 7 |
| New York | 1 | 12 |
| Newark | 1 | 12 |
| San Francisco | 2 | 4 |

## Warmest and coldest completed days

By daily average temperature, within the current data window only. Model output, not climate records.

| City | Warmest day | Avg C | Coldest day | Avg C | Days compared |
| --- | --- | ---: | --- | ---: | ---: |
| Chicago | 2026-11-21 | 12.69 | 2026-11-23 | 1.32 | 19 |
| New York | 2026-11-23 | 15.39 | 2026-11-25 | 3.47 | 19 |
| Newark | 2026-11-23 | 15.54 | 2026-11-25 | 3.49 | 19 |
| San Francisco | 2026-11-11 | 16.03 | 2026-11-23 | 9.25 | 19 |

## Week over week temperature

Mean daily average temperature, latest 7 completed days vs the 7 before. Two short windows, model output.

| City | Latest 7 days (C) | Previous 7 days (C) | Change (C) |
| --- | ---: | ---: | ---: |
| Chicago | 5.38 | 6.61 | -1.23 |
| New York | 9.96 | 8.83 | +1.13 |
| Newark | 9.75 | 8.7 | +1.05 |
| San Francisco | 11.19 | 11.62 | -0.43 |

## Degree days (base 18 C)

Heating degree days sum how far each completed day's average fell below 18 C; cooling degree days the reverse. Illustrative base, model output, current window only.

| City | Days | Heating degree days | Cooling degree days |
| --- | ---: | ---: | ---: |
| Chicago | 19 | 225.3 | 0.0 |
| New York | 19 | 156.2 | 0.0 |
| Newark | 19 | 159.8 | 0.0 |
| San Francisco | 19 | 105.7 | 0.0 |

## Wettest completed days

Model output, current window only.

| City | Day | Precip (mm) |
| --- | --- | ---: |
| San Francisco | 2026-11-18 | 46.4 |
| Newark | 2026-11-26 | 43.5 |
| New York | 2026-11-26 | 40.8 |
| Newark | 2026-11-12 | 31.3 |
| New York | 2026-11-12 | 21.7 |

## Windiest completed days

Maximum hourly wind speed. Model output, current window only.

| City | Day | Max wind (km/h) |
| --- | --- | ---: |
| New York | 2026-11-26 | 42.0 |
| Newark | 2026-11-26 | 40.0 |
| Chicago | 2026-11-27 | 36.7 |
| Chicago | 2026-11-26 | 36.7 |
| Newark | 2026-11-12 | 30.1 |

## Day-to-day temperature volatility

Mean absolute change in daily average temperature between consecutive completed days. Model output, current window only.

| City | Day pairs | Mean change (C) | Largest swing (C) | On |
| --- | ---: | ---: | ---: | --- |
| Chicago | 18 | 1.97 | 7.83 | 2026-11-23 |
| New York | 18 | 2.27 | 8.59 | 2026-11-24 |
| Newark | 18 | 2.22 | 8.42 | 2026-11-24 |
| San Francisco | 18 | 0.89 | 2.27 | 2026-11-24 |

## Frost days (minimum at or below 0 C)

Completed days only. Model output, current window only.

| City | Days | Frost days | Share | Coldest minimum (C) | On |
| --- | ---: | ---: | ---: | ---: | --- |
| Chicago | 19 | 5 | 26.3% | -1.8 | 2026-11-24 |
| New York | 19 | 1 | 5.3% | -0.1 | 2026-11-25 |
| Newark | 19 | 1 | 5.3% | -0.3 | 2026-11-25 |
| San Francisco | 19 | 0 | 0.0% | 5.5 | 2026-11-23 |

## City temperature co-movement

Pearson r of daily mean temperature over shared completed days. Short window, model output: descriptive only, not a climate relationship.

| City A | City B | Shared days | r |
| --- | --- | ---: | ---: |
| New York | Newark | 19 | 0.997 |
| Chicago | New York | 19 | 0.585 |
| Chicago | Newark | 19 | 0.549 |
| Chicago | San Francisco | 19 | -0.147 |
| New York | San Francisco | 19 | -0.186 |
| Newark | San Francisco | 19 | -0.19 |

## Data coverage

Completed days only. A short day has fewer than 24 hourly readings; any gaps would bias the daily statistics above.

| City | Days | Short days | Missing hours |
| --- | ---: | ---: | ---: |
| Chicago | 19 | 0 | 0 |
| New York | 19 | 0 | 0 |
| Newark | 19 | 0 | 0 |
| San Francisco | 19 | 0 | 0 |

## Daily temperature range

Maximum minus minimum temperature per completed day. Model output, current window only.

| City | Days | Mean range (C) | Widest (C) | On |
| --- | ---: | ---: | ---: | --- |
| Chicago | 19 | 8.8 | 13.5 | 2026-11-20 |
| New York | 19 | 8.6 | 14.0 | 2026-11-20 |
| Newark | 19 | 9.4 | 16.2 | 2026-11-18 |
| San Francisco | 19 | 6.6 | 12.3 | 2026-11-10 |

## Breezy days (peak wind at or above 25 km/h)

Completed days only. The 25 km/h cut-off is an illustrative choice made after inspecting this sample (30 km/h showed no hits in it), not an established standard or advisory level; zero hits is a valid result. Model output, current window only.

| City | Days | Breezy days | Share | Peak (km/h) | On |
| --- | ---: | ---: | ---: | ---: | --- |
| Chicago | 19 | 6 | 31.6% | 36.7 | 2026-11-26 |
| New York | 19 | 3 | 15.8% | 42.0 | 2026-11-26 |
| Newark | 19 | 3 | 15.8% | 40.0 | 2026-11-26 |
| San Francisco | 19 | 1 | 5.3% | 29.3 | 2026-11-18 |

## Temperature drift over the window

Least-squares slope of daily mean temperature over completed days. A short autumn window of model output: descriptive only, mostly seasonal, not a climate trend.

| City | Days | Slope (C/day) | Fitted change (C) |
| --- | ---: | ---: | ---: |
| Chicago | 19 | -0.085 | -1.5 |
| New York | 19 | -0.055 | -1.0 |
| Newark | 19 | -0.061 | -1.1 |
| San Francisco | 19 | -0.259 | -4.7 |

## Wet-day frequency and intensity

Wet day = 1 mm or more of total rain (illustrative, same cut-off as the dry streaks). Completed days only. Model output, current window only.

| City | Days | Wet days | Share | Mean rain on wet days (mm) |
| --- | ---: | ---: | ---: | ---: |
| Chicago | 19 | 7 | 36.8% | 5.8 |
| New York | 19 | 3 | 15.8% | 22.0 |
| Newark | 19 | 3 | 15.8% | 26.1 |
| San Francisco | 19 | 10 | 52.6% | 10.4 |

## Daily peak wind summary

Mean and 90th percentile (nearest rank) of each completed day's peak hourly wind. Model output, current window only.

| City | Days | Mean peak (km/h) | 90th percentile (km/h) |
| --- | ---: | ---: | ---: |
| Chicago | 19 | 20.2 | 36.7 |
| New York | 19 | 19.2 | 29.9 |
| Newark | 19 | 19.4 | 30.1 |
| San Francisco | 19 | 13.9 | 21.9 |

![Total rain per city](rain_totals.png)


![Daily temperature range by city](temp_range_by_city.png)


## Severe-weather days

![Daily peak wind by city](wind_by_city.png)

Daily rain >= 10 mm or wind >= 50 km/h. Illustrative thresholds, not official weather alerts. Values are Open-Meteo model output in mm and km/h per city-local day, not gauge observations; a day still in progress includes forecast hours.

| city | day | precip mm | max wind km/h | why | day status |
| --- | --- | ---: | ---: | --- | --- |
| Chicago | 2026-11-26 | 12.7 | 36.7 | heavy rain | complete |
| New York | 2026-11-26 | 40.8 | 42.0 | heavy rain | complete |
| Newark | 2026-11-26 | 43.5 | 40.0 | heavy rain | complete |
| San Francisco | 2026-11-19 | 10.1 | 15.9 | heavy rain | complete |
| San Francisco | 2026-11-18 | 46.4 | 29.3 | heavy rain | complete |
| Chicago | 2026-11-13 | 10.5 | 26.7 | heavy rain | complete |
| San Francisco | 2026-11-13 | 13.8 | 21.9 | heavy rain | complete |
| New York | 2026-11-12 | 21.7 | 24.5 | heavy rain | complete |

![Average temperature by city](avg_temp_by_city.png)

Data: [Open-Meteo](https://open-meteo.com/) hourly forecast API (past days are model `past_days` output, not observations).
