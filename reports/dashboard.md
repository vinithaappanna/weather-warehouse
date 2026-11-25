# Weather Warehouse - daily dashboard

Generated 2026-11-25 20:04 UTC.

| city | day | avg_temp_c | min_temp_c | max_temp_c | total_precip_mm | max_wind_kmh | hours_observed |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Chicago | 2026-11-25 | 3.17 | 0.7 | 4.7 | 0.0 | 29.0 | 24 |
| New York | 2026-11-25 | 3.36 | -0.1 | 6.3 | 0.0 | 18.7 | 24 |
| Newark | 2026-11-25 | 3.58 | -0.3 | 7.7 | 0.0 | 17.4 | 24 |
| San Francisco | 2026-11-25 | 13.13 | 11.5 | 15.5 | 3.3 | 11.1 | 24 |
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
| Newark | 2026-11-21 | 12.23 | 6.7 | 19.2 | 0.0 | 13.0 | 24 |
| San Francisco | 2026-11-21 | 9.53 | 6.4 | 12.1 | 8.0 | 14.3 | 24 |
| Chicago | 2026-11-20 | 11.73 | 5.5 | 19.0 | 0.0 | 17.1 | 24 |
| New York | 2026-11-20 | 13.37 | 7.3 | 21.3 | 0.0 | 9.5 | 24 |
| Newark | 2026-11-20 | 12.92 | 5.6 | 21.7 | 0.0 | 11.2 | 24 |
| San Francisco | 2026-11-20 | 10.15 | 8.0 | 13.2 | 1.4 | 10.9 | 24 |
| Chicago | 2026-11-19 | 11.13 | 6.0 | 18.6 | 0.0 | 20.8 | 24 |
| New York | 2026-11-19 | 10.98 | 5.9 | 18.6 | 0.0 | 8.6 | 24 |
| Newark | 2026-11-19 | 10.61 | 3.7 | 19.9 | 0.0 | 9.1 | 24 |
| San Francisco | 2026-11-19 | 10.85 | 8.8 | 12.7 | 10.1 | 15.9 | 24 |
| Chicago | 2026-11-18 | 7.84 | 2.6 | 15.5 | 0.0 | 18.4 | 24 |
| New York | 2026-11-18 | 10.6 | 5.1 | 18.4 | 0.0 | 9.3 | 24 |

## Heat / cold exposure (current window)

Hours at or above 30C / at or below 0C and degree-hours beyond each threshold. Illustrative thresholds, not clinical guidance.

| city | heat hours | cold hours | heat degree-hours | cold degree-hours |
| --- | ---: | ---: | ---: | ---: |
| Chicago | 0 | 19 | 0.0 | 20.3 |
| New York | 0 | 3 | 0.0 | 0.2 |
| Newark | 0 | 3 | 0.0 | 0.8 |
| San Francisco | 0 | 0 | 0.0 | 0.0 |

## Precipitation

Model output in mm over the window; the current day includes forecast hours.

![Daily precipitation by city](precip_by_city.png)

| city | total mm | wet days (>=1 mm) |
| --- | ---: | ---: |
| San Francisco | 104.1 | 10 |
| Newark | 34.7 | 2 |
| New York | 25.3 | 2 |
| Chicago | 18.5 | 5 |

## City leaders, 2026-11-24 (latest day complete in every city)

Model output, not station readings.

- Warmest high: San Francisco (14.9 C)
- Coldest low: Chicago (-1.8 C)
- Wettest: San Francisco (5.0 mm)
- Windiest: Newark (24.6 km/h)

## Source freshness

Last successful Open-Meteo fetch per city (empty or failed fetches do not count). The latest hour is normally ahead of now because the feed includes forecast hours.

| City | Last successful fetch | Age (h) | Failed fetches since | Latest hour held |
| --- | --- | ---: | ---: | --- |
| Chicago | 2026-11-25 15:04:08.036621 | 0.0 | 0 | 2026-11-25 23:00:00 |
| New York | 2026-11-25 15:04:08.036621 | 0.0 | 0 | 2026-11-25 23:00:00 |
| Newark | 2026-11-25 15:04:08.036621 | 0.0 | 0 | 2026-11-25 23:00:00 |
| San Francisco | 2026-11-25 15:04:08.036621 | 0.0 | 0 | 2026-11-25 23:00:00 |

## Dry-day streaks (rain under 1 mm)

Consecutive completed days below 1 mm of rain. Model output; illustrative, not a drought measure.

| City | Current streak (days) | Longest streak (days) |
| --- | ---: | ---: |
| Chicago | 2 | 7 |
| New York | 11 | 11 |
| Newark | 11 | 11 |
| San Francisco | 0 | 4 |

## Warmest and coldest completed days

By daily average temperature, within the current data window only. Model output, not climate records.

| City | Warmest day | Avg C | Coldest day | Avg C | Days compared |
| --- | --- | ---: | --- | ---: | ---: |
| Chicago | 2026-11-21 | 12.69 | 2026-11-23 | 1.32 | 16 |
| New York | 2026-11-23 | 15.39 | 2026-11-14 | 4.66 | 16 |
| Newark | 2026-11-23 | 15.54 | 2026-11-14 | 4.75 | 16 |
| San Francisco | 2026-11-11 | 16.03 | 2026-11-23 | 9.25 | 16 |

## Week over week temperature

Mean daily average temperature, latest 7 completed days vs the 7 before. Two short windows, model output.

| City | Latest 7 days (C) | Previous 7 days (C) | Change (C) |
| --- | ---: | ---: | ---: |
| Chicago | 7.89 | 4.4 | +3.48 |
| New York | 11.95 | 8.11 | +3.85 |
| Newark | 11.75 | 7.97 | +3.78 |
| San Francisco | 10.43 | 13.49 | -3.06 |

## Degree days (base 18 C)

Heating degree days sum how far each completed day's average fell below 18 C; cooling degree days the reverse. Illustrative base, model output, current window only.

| City | Days | Heating degree days | Cooling degree days |
| --- | ---: | ---: | ---: |
| Chicago | 16 | 184.5 | 0.0 |
| New York | 16 | 123.3 | 0.0 |
| Newark | 16 | 125.8 | 0.0 |
| San Francisco | 16 | 89.6 | 0.0 |

## Wettest completed days

Model output, current window only.

| City | Day | Precip (mm) |
| --- | --- | ---: |
| San Francisco | 2026-11-18 | 46.4 |
| Newark | 2026-11-12 | 31.3 |
| New York | 2026-11-12 | 21.7 |
| San Francisco | 2026-11-13 | 13.8 |
| Chicago | 2026-11-13 | 10.5 |

## Windiest completed days

Maximum hourly wind speed. Model output, current window only.

| City | Day | Max wind (km/h) |
| --- | --- | ---: |
| Newark | 2026-11-12 | 30.1 |
| New York | 2026-11-09 | 29.9 |
| Chicago | 2026-11-11 | 29.4 |
| San Francisco | 2026-11-18 | 29.3 |
| Newark | 2026-11-09 | 26.8 |

## Day-to-day temperature volatility

Mean absolute change in daily average temperature between consecutive completed days. Model output, current window only.

| City | Day pairs | Mean change (C) | Largest swing (C) | On |
| --- | ---: | ---: | ---: | --- |
| Chicago | 15 | 1.99 | 7.83 | 2026-11-23 |
| New York | 15 | 2.03 | 8.59 | 2026-11-24 |
| Newark | 15 | 1.97 | 8.42 | 2026-11-24 |
| San Francisco | 15 | 0.89 | 2.27 | 2026-11-24 |

## Frost days (minimum at or below 0 C)

Completed days only. Model output, current window only.

| City | Days | Frost days | Share | Coldest minimum (C) | On |
| --- | ---: | ---: | ---: | ---: | --- |
| Chicago | 16 | 5 | 31.2% | -1.8 | 2026-11-24 |
| New York | 16 | 0 | 0.0% | 2.1 | 2026-11-16 |
| Newark | 16 | 0 | 0.0% | 1.9 | 2026-11-16 |
| San Francisco | 16 | 0 | 0.0% | 5.5 | 2026-11-23 |

## City temperature co-movement

Pearson r of daily mean temperature over shared completed days. Short window, model output: descriptive only, not a climate relationship.

| City A | City B | Shared days | r |
| --- | --- | ---: | ---: |
| New York | Newark | 16 | 0.998 |
| Chicago | New York | 16 | 0.582 |
| Chicago | Newark | 16 | 0.542 |
| Chicago | San Francisco | 16 | -0.139 |
| New York | San Francisco | 16 | -0.169 |
| Newark | San Francisco | 16 | -0.175 |

![Total rain per city](rain_totals.png)


![Daily temperature range by city](temp_range_by_city.png)


## Severe-weather days

![Daily peak wind by city](wind_by_city.png)

Daily rain >= 10 mm or wind >= 50 km/h. Illustrative thresholds, not official weather alerts. Values are Open-Meteo model output in mm and km/h per city-local day, not gauge observations; a day still in progress includes forecast hours.

| city | day | precip mm | max wind km/h | why | day status |
| --- | --- | ---: | ---: | --- | --- |
| San Francisco | 2026-11-19 | 10.1 | 15.9 | heavy rain | complete |
| San Francisco | 2026-11-18 | 46.4 | 29.3 | heavy rain | complete |
| Chicago | 2026-11-13 | 10.5 | 26.7 | heavy rain | complete |
| San Francisco | 2026-11-13 | 13.8 | 21.9 | heavy rain | complete |
| New York | 2026-11-12 | 21.7 | 24.5 | heavy rain | complete |
| Newark | 2026-11-12 | 31.3 | 30.1 | heavy rain | complete |

![Average temperature by city](avg_temp_by_city.png)

Data: [Open-Meteo](https://open-meteo.com/) hourly forecast API (past days are model `past_days` output, not observations).
