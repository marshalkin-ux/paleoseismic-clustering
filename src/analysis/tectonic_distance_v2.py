"""Тектоническое расстояние с учётом типа границы плит.

Улучшенная версия ``TectonicDistanceCalculator``: рёбра графа взвешиваются
не только гаверсинусным расстоянием, но и коэффициентом типа границы.
Зоны субдукции передают напряжение эффективнее спрединговых хребтов,
поэтому «тектоническая цена» пути через них ниже.
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any

import networkx as nx
import numpy as np
import pandas as pd

logger = logging.getLogger(__name__)

_R_EARTH = 6371.0  # км

# ---------------------------------------------------------------------------
# Весовые коэффициенты по типу границы
# ---------------------------------------------------------------------------

#: Коэффициенты для типов границ.
#: Меньше = эффективнее передача напряжения = «ближе» в тектоническом смысле.
BOUNDARY_WEIGHTS: dict[str, float] = {
    "subduction": 1.0,   # зоны субдукции — максимальная передача напряжения
    "transform": 1.2,    # трансформные разломы
    "collision": 1.1,    # коллизионные зоны
    "spreading": 1.5,    # спрединговые хребты — наименее эффективны
    "unknown": 1.3,      # неопределённый тип
}


def _haversine_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Расстояние по формуле гаверсинуса (км)."""
    lat1, lon1, lat2, lon2 = map(np.radians, [lat1, lon1, lat2, lon2])
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    a = np.sin(dlat / 2) ** 2 + np.cos(lat1) * np.cos(lat2) * np.sin(dlon / 2) ** 2
    return 2 * _R_EARTH * np.arcsin(np.sqrt(a))


# ---------------------------------------------------------------------------
# Улучшенный калькулятор
# ---------------------------------------------------------------------------

class TectonicDistanceV2:
    """Улучшенный калькулятор тектонического расстояния.

    Граф строится с весами рёбер::

        weight = haversine_km(A, B) * BOUNDARY_WEIGHTS[boundary_type]

    Это означает, что пути через зоны субдукции «короче» в тектоническом
    смысле, чем пути через спрединговые хребты.

    Пример::

        calc = TectonicDistanceV2()
        calc.build_graph()
        dist = calc.tectonic_distance_v2(35.0, 139.0, -33.5, -70.5)
        btype = calc.boundary_type_for_pair(35.0, 139.0, -33.5, -70.5)
    """

    #: 20 сегментов с указанием типа границы: (name, type, [(lat, lon), ...])
    PLATE_BOUNDARIES: list[tuple[str, str, list[tuple[float, float]]]] = [
        ("Cascadia", "subduction", [
            (48, -125), (46, -124), (44, -124), (42, -124), (40, -124),
        ]),
        ("Japan_Trench", "subduction", [
            (42, 143), (40, 142), (38, 142), (36, 141), (34, 140),
        ]),
        ("Tonga_Trench", "subduction", [
            (-15, -174), (-18, -175), (-21, -174), (-24, -175),
        ]),
        ("Chile_Trench", "subduction", [
            (-18, -70), (-22, -70), (-26, -70), (-30, -71),
            (-34, -72), (-38, -73), (-42, -74),
        ]),
        ("Aleutian", "subduction", [
            (52, -172), (54, -165), (56, -156), (58, -148),
        ]),
        ("Sumatra_Java", "subduction", [
            (5, 95), (0, 100), (-5, 105), (-10, 110),
        ]),
        ("Central_America", "subduction", [
            (15, -92), (12, -89), (9, -84), (8, -77),
        ]),
        ("Philippines", "subduction", [
            (20, 122), (15, 120), (10, 125),
        ]),
        ("San_Andreas", "transform", [
            (37, -122), (36, -120), (34, -118), (33, -116),
        ]),
        ("Alpine", "transform", [
            (-43, 171), (-44, 170), (-46, 168),
        ]),
        ("NAT_Ridge", "spreading", [
            (65, -18), (60, -28), (50, -35), (40, -35), (30, -42), (20, -45),
        ]),
        ("SAT_Ridge", "spreading", [
            (0, -30), (-10, -14), (-20, -13), (-30, -14), (-40, -15), (-50, -8),
        ]),
        ("Indian_Ridge", "spreading", [
            (-20, 65), (-30, 70), (-40, 75), (-50, 70),
        ]),
        ("Pacific_Ridge", "spreading", [
            (-5, -105), (-15, -110), (-25, -112), (-35, -109), (-45, -110),
        ]),
        ("Himalaya", "collision", [
            (30, 80), (32, 85), (28, 90), (26, 95),
        ]),
        ("Zagros", "collision", [
            (30, 50), (32, 54), (34, 57), (36, 60),
        ]),
        ("Caribbean", "transform", [
            (15, -63), (16, -66), (18, -72), (20, -76),
        ]),
        ("Scotia", "transform", [
            (-54, -28), (-56, -34), (-57, -40), (-56, -45),
        ]),
        ("Mariana", "subduction", [
            (20, 145), (18, 146), (15, 147), (12, 145),
        ]),
        ("Ryukyu", "subduction", [
            (30, 130), (28, 128), (26, 127), (24, 123),
        ]),
    ]

    def __init__(self) -> None:
        self._graph: nx.Graph | None = None
        self._node_coords: list[tuple[float, float]] = []
        self._node_types: list[str] = []   # тип границы для каждого узла
        self._node_array: np.ndarray | None = None

    def build_graph(self, resolution_deg: float = 1.0) -> nx.Graph:
        """Строит граф NetworkX с взвешенными рёбрами.

        Вес ребра = haversine_km(A, B) * BOUNDARY_WEIGHTS[boundary_type].

        Args:
            resolution_deg: шаг интерполяции узлов вдоль границы (градусы).

        Returns:
            Построенный граф (также сохраняется в ``self._graph``).
        """
        self._graph = nx.Graph()
        self._node_coords = []
        self._node_types = []
        node_id = 0

        for seg_name, seg_type, coords in self.PLATE_BOUNDARIES:
            bw = BOUNDARY_WEIGHTS.get(seg_type, BOUNDARY_WEIGHTS["unknown"])
            prev_node: int | None = None

            for pt in coords:
                if prev_node is not None:
                    prev_lat, prev_lon = self._node_coords[prev_node]
                    dist_seg = _haversine_km(prev_lat, prev_lon, pt[0], pt[1])
                    n_interp = max(1, int(dist_seg / (resolution_deg * 111.0)))

                    for k in range(1, n_interp):
                        frac = k / n_interp
                        ilat = prev_lat + frac * (pt[0] - prev_lat)
                        ilon = prev_lon + frac * (pt[1] - prev_lon)
                        self._node_coords.append((ilat, ilon))
                        self._node_types.append(seg_type)
                        self._graph.add_node(
                            node_id, lat=ilat, lon=ilon, boundary_type=seg_type,
                        )
                        # Ребро к предыдущему узлу
                        prev_lat_n, prev_lon_n = self._node_coords[node_id - 1]
                        raw_w = _haversine_km(prev_lat_n, prev_lon_n, ilat, ilon)
                        self._graph.add_edge(
                            node_id - 1, node_id,
                            weight=raw_w * bw,
                            boundary_type=seg_type,
                        )
                        prev_node = node_id
                        node_id += 1

                self._node_coords.append((pt[0], pt[1]))
                self._node_types.append(seg_type)
                self._graph.add_node(
                    node_id, lat=pt[0], lon=pt[1], boundary_type=seg_type,
                )
                if prev_node is not None:
                    prev_lat_n, prev_lon_n = self._node_coords[prev_node]
                    raw_w = _haversine_km(prev_lat_n, prev_lon_n, pt[0], pt[1])
                    self._graph.add_edge(
                        prev_node, node_id,
                        weight=raw_w * bw,
                        boundary_type=seg_type,
                    )
                prev_node = node_id
                node_id += 1

        self._node_array = np.array(self._node_coords)
        logger.info(
            "TectonicDistanceV2: %d узлов, %d рёбер",
            self._graph.number_of_nodes(),
            self._graph.number_of_edges(),
        )
        return self._graph

    def _nearest_node(self, lat: float, lon: float) -> int:
        """Индекс ближайшего узла графа к точке (lat, lon)."""
        if self._node_array is None:
            raise RuntimeError("Граф не построен. Вызовите build_graph().")
        dists = _haversine_km(lat, lon, self._node_array[:, 0], self._node_array[:, 1])
        return int(np.argmin(dists))

    def tectonic_distance_v2(
        self,
        lat1: float,
        lon1: float,
        lat2: float,
        lon2: float,
        max_boundary_dist_km: float = 500.0,
    ) -> float:
        """Взвешенное тектоническое расстояние между двумя точками.

        Использует алгоритм Дейкстры на взвешенном графе.

        Args:
            lat1, lon1: координаты первой точки.
            lat2, lon2: координаты второй точки.
            max_boundary_dist_km: порог для фолбэка на гаверсинус × 1.5.

        Returns:
            Взвешенное расстояние (км, условные единицы с учётом типа границы).
        """
        if self._graph is None:
            self.build_graph()

        n1 = self._nearest_node(lat1, lon1)
        n2 = self._nearest_node(lat2, lon2)

        d1 = _haversine_km(lat1, lon1, *self._node_coords[n1])
        d2 = _haversine_km(lat2, lon2, *self._node_coords[n2])

        if d1 > max_boundary_dist_km or d2 > max_boundary_dist_km:
            return _haversine_km(lat1, lon1, lat2, lon2) * 1.5

        try:
            path_len = nx.dijkstra_path_length(self._graph, n1, n2, weight="weight")
            return float(d1 + path_len + d2)
        except nx.NetworkXNoPath:
            return _haversine_km(lat1, lon1, lat2, lon2) * 1.5

    # Псевдоним для совместимости с SeismicClusterAnalyzer
    def tectonic_distance(
        self,
        lat1: float,
        lon1: float,
        lat2: float,
        lon2: float,
        max_boundary_dist_km: float = 500.0,
    ) -> float:
        """Псевдоним для ``tectonic_distance_v2``."""
        return self.tectonic_distance_v2(lat1, lon1, lat2, lon2, max_boundary_dist_km)

    def boundary_type_for_pair(
        self,
        lat1: float,
        lon1: float,
        lat2: float,
        lon2: float,
    ) -> str:
        """Определяет доминирующий тип границы для пары событий.

        Возвращает тип границы ближайшего узла к средней точке.

        Args:
            lat1, lon1: координаты первого события.
            lat2, lon2: координаты второго события.

        Returns:
            Строка типа границы: ``'subduction'``, ``'transform'``,
            ``'spreading'``, ``'collision'``, ``'unknown'``.
        """
        if self._node_array is None:
            self.build_graph()

        # Средняя точка
        mid_lat = (lat1 + lat2) / 2
        mid_lon = (lon1 + lon2) / 2
        nearest = self._nearest_node(mid_lat, mid_lon)
        return self._node_types[nearest]

    def compare_distances(
        self,
        lat1: float,
        lon1: float,
        lat2: float,
        lon2: float,
    ) -> dict:
        """Сравнивает три варианта расстояния между двумя точками.

        Полезно для отладки и понимания вклада тектонической структуры.

        Args:
            lat1, lon1: координаты первой точки.
            lat2, lon2: координаты второй точки.

        Returns:
            Словарь::

                {
                    'euclidean_km': float,          # гаверсинусное расстояние
                    'tectonic_v1_km': float,         # через граф без весов границ
                    'tectonic_v2_km': float,         # с весами по типу границы
                    'dominant_boundary_type': str,   # тип границы на пути
                    'ratio_tect_eucl': float,        # tectonic_v2 / euclidean
                }
        """
        if self._graph is None:
            self.build_graph()

        eucl = _haversine_km(lat1, lon1, lat2, lon2)

        # v1: Дейкстра по графу с единичными весами (только расстояние км)
        n1 = self._nearest_node(lat1, lon1)
        n2 = self._nearest_node(lat2, lon2)
        d1_snap = _haversine_km(lat1, lon1, *self._node_coords[n1])
        d2_snap = _haversine_km(lat2, lon2, *self._node_coords[n2])

        try:
            path_len_raw = nx.dijkstra_path_length(
                self._graph, n1, n2, weight=lambda u, v, d: _haversine_km(
                    self._node_coords[u][0], self._node_coords[u][1],
                    self._node_coords[v][0], self._node_coords[v][1],
                ),
            )
            tect_v1 = float(d1_snap + path_len_raw + d2_snap)
        except nx.NetworkXNoPath:
            tect_v1 = eucl * 1.5

        tect_v2 = self.tectonic_distance_v2(lat1, lon1, lat2, lon2)
        btype = self.boundary_type_for_pair(lat1, lon1, lat2, lon2)

        return {
            "euclidean_km": float(eucl),
            "tectonic_v1_km": float(tect_v1),
            "tectonic_v2_km": float(tect_v2),
            "dominant_boundary_type": btype,
            "ratio_tect_eucl": float(tect_v2 / eucl) if eucl > 0 else float("nan"),
        }

    def batch_tectonic_distances_parallel(
        self,
        events_df: pd.DataFrame,
        n_workers: int = 4,
        max_events: int = 200,
    ) -> np.ndarray:
        """Параллельное вычисление матрицы тектонических расстояний.

        Разделяет задачу по строкам матрицы между процессами через
        ``multiprocessing.Pool``. На небольших каталогах (≤ 50 событий)
        автоматически переключается на однопоточный режим.

        Args:
            events_df: DataFrame с колонками ``lat``/``latitude``,
                       ``lon``/``longitude``.
            n_workers: число рабочих процессов.
            max_events: максимальный размер подвыборки.

        Returns:
            Симметричная матрица расстояний (n × n).
        """
        if self._graph is None:
            self.build_graph()

        lat_col = "latitude" if "latitude" in events_df.columns else "lat"
        lon_col = "longitude" if "longitude" in events_df.columns else "lon"

        sub = events_df.head(max_events)
        n = len(sub)
        coords = sub[[lat_col, lon_col]].values.astype(float)

        # Для маленьких каталогов параллелизм не нужен
        if n <= 50 or n_workers <= 1:
            return self.batch_distance_matrix(events_df, max_events=max_events)

        dist_matrix = np.zeros((n, n))

        def _compute_row(i: int) -> tuple[int, np.ndarray]:
            row = np.zeros(n)
            for j in range(i + 1, n):
                row[j] = self.tectonic_distance_v2(
                    coords[i, 0], coords[i, 1],
                    coords[j, 0], coords[j, 1],
                )
            return i, row

        try:
            from multiprocessing import Pool
            with Pool(processes=min(n_workers, n)) as pool:
                results = pool.map(_compute_row, range(n))
            for i, row in results:
                dist_matrix[i, i + 1:] = row[i + 1:]
                dist_matrix[i + 1:, i] = row[i + 1:]
        except Exception as exc:
            logger.warning("Параллельное вычисление недоступно (%s), переключаюсь на однопоточное.", exc)
            return self.batch_distance_matrix(events_df, max_events=max_events)

        logger.info(
            "batch_tectonic_distances_parallel: матрица %dx%d вычислена (%d воркеров)",
            n, n, n_workers,
        )
        return dist_matrix

    def batch_distance_matrix(
        self,
        events_df: pd.DataFrame,
        max_events: int = 200,
    ) -> np.ndarray:
        """Матрица взвешенных тектонических расстояний для подвыборки событий.

        Args:
            events_df: DataFrame с колонками ``lat``/``latitude``,
                       ``lon``/``longitude``.
            max_events: максимальный размер подвыборки.

        Returns:
            Симметричная матрица расстояний (n × n).
        """
        if self._graph is None:
            self.build_graph()

        lat_col = "latitude" if "latitude" in events_df.columns else "lat"
        lon_col = "longitude" if "longitude" in events_df.columns else "lon"

        sub = events_df.head(max_events)
        n = len(sub)
        coords = sub[[lat_col, lon_col]].values
        dist_matrix = np.zeros((n, n))

        for i in range(n):
            for j in range(i + 1, n):
                d = self.tectonic_distance_v2(
                    coords[i, 0], coords[i, 1],
                    coords[j, 0], coords[j, 1],
                )
                dist_matrix[i, j] = d
                dist_matrix[j, i] = d

        return dist_matrix
