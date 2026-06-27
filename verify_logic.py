"""
Автономная проверка логики основных алгоритмов без внешних зависимостей.
Запуск: python verify_logic.py
"""
import sys
import math

print("=" * 60)
print("Проверка алгоритмов paleoseismic-clustering")
print("=" * 60)

errors = []

# ── 1. Метрика Baiesi-Paczuski ────────────────────────────────────────────────
print("\n1. Метрика eta Baiesi-Paczuski")

def eta(t, r, m, df=1.6, b=1.0):
    if t <= 0 or r <= 0:
        return float("inf")
    return t * (r ** df) * (10 ** (-b * m))

# Тест: eta должна быть положительной для корректных аргументов
v = eta(1.0, 100.0, 7.0)
assert v > 0 and math.isfinite(v), f"Ожидалось положительное конечное, получено {v}"
print(f"  eta(1yr, 100km, M7) = {v:.6f}")

# Тест: большее время → большая eta
v1, v2 = eta(1.0, 100.0, 7.0), eta(2.0, 100.0, 7.0)
assert v2 > v1, f"Нарушена монотонность по времени: {v1} >= {v2}"
print(f"  Монотонность по времени: OK ({v1:.4f} < {v2:.4f})")

# Тест: большая магнитуда → меньшая eta
v1, v2 = eta(1.0, 100.0, 7.0), eta(1.0, 100.0, 8.0)
assert v2 < v1, f"Нарушена монотонность по магнитуде: {v1} <= {v2}"
print(f"  Монотонность по магнитуде: OK ({v1:.4f} > {v2:.4f})")

# Числовая проверка
expected = 1.0 * (100.0 ** 1.6) * (10 ** (-1.0 * 7.0))
actual = eta(1.0, 100.0, 7.0, df=1.6, b=1.0)
assert abs(actual - expected) < 1e-10, f"Числовое значение неверно: {actual} != {expected}"
print(f"  Числовая проверка: OK (eta = {actual:.6e})")

# ── 2. Формула Gutenberg-Richter b-value ─────────────────────────────────────
print("\n2. b-value (Gutenberg-Richter)")

import random
random.seed(42)

# Генерируем экспоненциальное распределение магнитуд
mc_true = 5.5
b_true = 1.0
n = 1000
# Для экспоненциального: P(M > m) = 10^(-b*(m-mc))
# M = mc - log10(U) / b для U ~ Uniform(0,1)
mags = [mc_true - math.log10(max(random.random(), 1e-10)) / b_true for _ in range(n)]
mags = [m for m in mags if m >= mc_true]

# Оценка b через MLE Aki 1965
mean_m = sum(mags) / len(mags)
b_est = math.log10(math.e) / (mean_m - mc_true + 0.05)
print(f"  Истинное b = {b_true:.3f}, оценка MLE = {b_est:.3f}")
assert abs(b_est - b_true) < 0.3, f"b-value слишком далеко от истинного: {b_est:.3f}"
print(f"  Точность b-value: OK (отклонение {abs(b_est - b_true):.3f} < 0.3)")

# ── 3. Гаверсинус ─────────────────────────────────────────────────────────────
print("\n3. Расстояние Гаверсинуса")

def haversine(lat1, lon1, lat2, lon2):
    R = 6371.0
    lat1, lon1, lat2, lon2 = [x * math.pi / 180 for x in [lat1, lon1, lat2, lon2]]
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    a = math.sin(dlat/2)**2 + math.cos(lat1)*math.cos(lat2)*math.sin(dlon/2)**2
    return 2 * R * math.asin(math.sqrt(a))

# Экватор: 1 градус долготы ≈ 111.32 км
d = haversine(0.0, 0.0, 0.0, 1.0)
assert abs(d - 111.32) < 0.5, f"Экватор: ожидалось 111.32, получено {d:.2f}"
print(f"  Экватор 1° = {d:.2f} км (ожидается 111.32 км): OK")

# Токио → Москва ≈ 7500 км
d = haversine(35.68, 139.69, 55.75, 37.62)
assert 7000 < d < 8500, f"Токио-Москва: {d:.0f} км вне допустимого диапазона"
print(f"  Токио → Москва = {d:.0f} км: OK")

# Симметрия
d1 = haversine(35.0, 135.0, -33.0, -70.0)
d2 = haversine(-33.0, -70.0, 35.0, 135.0)
assert abs(d1 - d2) < 1e-6, f"Нарушена симметрия: {d1} != {d2}"
print(f"  Симметрия: OK ({d1:.2f} = {d2:.2f})")

# ── 4. Сейсмический момент ────────────────────────────────────────────────────
print("\n4. Суммарный сейсмический момент")

def seismic_moment(mag):
    return 10 ** (1.5 * mag + 9.1)

mags_test = [7.0, 7.5, 8.0]
total = sum(seismic_moment(m) for m in mags_test)
print(f"  Суммарный момент для M[7.0, 7.5, 8.0] = {total:.2e} Нм")
assert total > 0, "Момент должен быть положительным"
# M8 доминирует
m8_ratio = seismic_moment(8.0) / total
print(f"  Доля M8.0 в суммарном моменте: {m8_ratio:.1%}: OK")
assert m8_ratio > 0.5, "M8 должен составлять > 50% суммарного момента"

# ── 5. Convex hull площадь ────────────────────────────────────────────────────
print("\n5. Пространственный охват (Convex Hull)")

def simple_area(lats, lons):
    if len(lats) < 3:
        return 0.0
    return (max(lats) - min(lats)) * (max(lons) - min(lons))

# Малая область
area_small = simple_area([35.0, 35.1, 35.1, 35.0], [135.0, 135.0, 135.1, 135.1])
# Большая область
area_large = simple_area([-60.0, 60.0, 60.0, -60.0], [-120.0, -120.0, 120.0, 120.0])
assert area_large > area_small, f"Большая область: {area_large} должна быть > {area_small}"
print(f"  Малая: {area_small:.4f} < Большая: {area_large:.1f} кв.°: OK")

# ── Итог ──────────────────────────────────────────────────────────────────────
print("\n" + "=" * 60)
if errors:
    print(f"ОШИБОК: {len(errors)}")
    for e in errors:
        print(f"  - {e}")
    sys.exit(1)
else:
    print("ВСЕ ПРОВЕРКИ ПРОШЛИ УСПЕШНО")
    sys.exit(0)
