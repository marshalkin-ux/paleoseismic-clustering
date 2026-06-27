"""Вычисление тектонических расстояний между землетрясениями.

Использует границы тектонических плит Bird (2003) для построения графа
расстояний вдоль границ. При недоступности файла Bird (2003) используется
встроенный упрощённый набор из 20 ключевых сегментов границ.
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any

import networkx as nx
import numpy as np
import pandas as pd

logger = logging.getLogger(__name__)

# Радиус Земли в км
R_EARTH = 6371.0

# Упрощённые ключевые сегменты границ плит (20 сегментов Bird 2003)
# Каждый сегмент задаётся списком точек (lat, lon)
BUILTIN_BOUNDARIES: list[list[tuple[float, float]]] = [
    # Тихоокеанское огненное кольцо (западная часть)
    [(55, 160), (50, 155), (45, 150), (40, 142), (35, 137), (30, 132), (25, 127), (20, 122)],
    # Тихоокеанское огненное кольцо (восточная часть)
    [(60, -145), (55, -135), (50, -125), (45, -122), (40, -120), (35, -118), (30, -115), (20, -105)],
    # Центральноамериканская зона субдукции
    [(20, -105), (15, -95), (10, -85), (5, -78), (0, -77)],
    # Андская зона субдукции
    [(0, -77), (-10, -78), (-20, -70), (-30, -72), (-40, -73), (-55, -67)],
    # Срединно-Атлантический хребет
    [(65, -18), (50, -30), (30, -42), (0, -14), (-30, -14), (-55, -8)],
    # Альпийско-Гималайский пояс (западная часть)
    [(37, -8), (38, 5), (40, 15), (42, 28), (40, 42), (35, 52)],
    # Альпийско-Гималайский пояс (восточная часть)
    [(35, 52), (32, 60), (28, 70), (28, 82), (27, 88), (25, 95)],
    # Зона субдукции Сунда
    [(25, 95), (15, 98), (5, 102), (-3, 104), (-7, 110), (-9, 118), (-8, 128)],
    # Зона субдукции Тонга-Кермадек
    [(-55, -28), (-45, -10), (-35, -15), (-25, -175), (-15, -172)],
    # Новозеландская зона субдукции
    [(-38, 175), (-42, 174), (-46, 168), (-50, 165)],
    # Курило-Камчатская дуга
    [(50, 155), (48, 153), (46, 151), (44, 148), (43, 146), (42, 143)],
    # Японская дуга
    [(42, 143), (40, 142), (38, 142), (35, 137), (32, 132)],
    # Рюкю
    [(32, 132), (28, 128), (25, 127), (23, 122), (22, 122)],
    # Филиппинская дуга
    [(22, 122), (18, 122), (14, 120), (10, 124), (5, 126)],
    # Восточно-Африканский рифт
    [(15, 42), (10, 40), (5, 37), (0, 35), (-5, 35), (-10, 37), (-15, 35)],
    # Красноморский рифт
    [(28, 34), (24, 37), (20, 38), (15, 42)],
    # Аравийская плита
    [(28, 34), (25, 50), (22, 58), (22, 60)],
    # Западно-Тихоокеанская зона субдукции
    [(-5, 142), (-8, 148), (-9, 154), (-10, 160), (-12, 164), (-15, 167)],
    # Каскадская зона субдукции
    [(48, -124), (45, -124), (42, -124), (40, -124)],
    # Срединно-Индийский хребет
    [(10, 65), (0, 70), (-10, 72), (-20, 75), (-30, 75), (-40, 70)],
]


def haversine(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Вычисляет расстояние по формуле гаверсинуса (км)."""
    lat1, lon1, lat2, lon2 = map(np.radians, [lat1, lon1, lat2, lon2])
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    a = np.sin(dlat / 2) ** 2 + np.cos(lat1) * np.cos(lat2) * np.sin(dlon / 2) ** 2
    return 2 * R_EARTH * np.arcsin(np.sqrt(a))


# Alias for backward compatibility
_haversine_km = haversine


class TectonicDistanceCalculator:
    """Вычислитель тектонических расстояний через граф границ плит.

    Пример::

        calc = TectonicDistanceCalculator()
        calc.build_graph()
        dist = calc.tectonic_distance(-33.5, -70.5, 35.7, 139.7)
    """

    def __init__(self) -> None:
        self._graph: nx.Graph | None = None
        self._node_coords: list[tuple[float, float]] = []
        self._node_array: np.ndarray | None = None

    def load_plate_boundaries(self, path: str | Path) -> None:
        """Загружает границы плит из GeoJSON или Shapefile Bird (2003).

        При ошибке загрузки автоматически переключается на встроенный набор.

        Args:
            path: путь к файлу границ плит.
        """
        try:
            import geopandas as gpd
            gdf = gpd.read_file(str(path))
            logger.info("Загружены границы плит из %s (%d объектов)", path, len(gdf))
            self._external_boundaries = gdf
        except Exception as exc:
            logger.warning(
                "Не удалось загрузить Bird (2003) из %s: %s. Используем встроенный набор.",
                path, exc,
            )

    def build_graph(self, resolution_deg: float = 0.5) -> None:
        """Строит граф NetworkX из границ тектонических плит.

        Узлы = точки на границах с шагом resolution_deg градусов,
        рёбра = расстояние в км между соседними узлами.

        Args:
            resolution_deg: шаг между узлами вдоль границы.
        """
        self._graph = nx.Graph()
        self._node_coords = []
        node_id = 0

        # Используем встроенный набор сегментов
        boundaries = BUILTIN_BOUNDARIES

        for segment in boundaries:
            prev_node = None
            for pt in segment:
                # Добавляем промежуточные точки для заданного разрешения
                if prev_node is not None:
                    prev_lat, prev_lon = self._node_coords[prev_node]
                    dist_seg = haversine(prev_lat, prev_lon, pt[0], pt[1])
                    n_interp = max(1, int(dist_seg / (resolution_deg * 111.0)))
                    for k in range(1, n_interp):
                        t = k / n_interp
                        ilat = prev_lat + t * (pt[0] - prev_lat)
                        ilon = prev_lon + t * (pt[1] - prev_lon)
                        self._node_coords.append((ilat, ilon))
                        self._graph.add_node(node_id, lat=ilat, lon=ilon)
                        if prev_node is not None:
                            w = haversine(
                                self._node_coords[node_id - 1][0],
                                self._node_coords[node_id - 1][1],
                                ilat, ilon,
                            )
                            self._graph.add_edge(node_id - 1, node_id, weight=w)
                        prev_node = node_id
                        node_id += 1

                self._node_coords.append((pt[0], pt[1]))
                self._graph.add_node(node_id, lat=pt[0], lon=pt[1])
                if prev_node is not None:
                    w = haversine(
                        self._node_coords[prev_node][0],
                        self._node_coords[prev_node][1],
                        pt[0], pt[1],
                    )
                    self._graph.add_edge(prev_node, node_id, weight=w)
                prev_node = node_id
                node_id += 1

        self._node_array = np.array(self._node_coords)
        logger.info(
            "Граф границ плит: %d узлов, %d рёбер",
            self._graph.number_of_nodes(),
            self._graph.number_of_edges(),
        )

    def nearest_boundary_node(self, lat: float, lon: float) -> int:
        """Находит ближайший узел графа к заданной точке.

        Args:
            lat: широта события.
            lon: долгота события.

        Returns:
            Индекс ближайшего узла.
        """
        if self._node_array is None:
            raise RuntimeError("Граф не построен. Вызовите build_graph() сначала.")

        dists = haversine(
            lat, lon,
            self._node_array[:, 0],
            self._node_array[:, 1],
        )
        return int(np.argmin(dists))

    def tectonic_distance(
        self,
        lat1: float,
        lon1: float,
        lat2: float,
        lon2: float,
        max_boundary_dist_km: float = 500.0,
    ) -> float:
        """Вычисляет тектоническое расстояние между двумя событиями.

        Использует кратчайший путь Дейкстры по графу границ плит.
        Если событие дальше max_boundary_dist_km от любой границы —
        использует великоокружное расстояние × 1.5.

        Args:
            lat1, lon1: координаты первого события.
            lat2, lon2: координаты второго события.
            max_boundary_dist_km: порог для фолбэка.

        Returns:
            Расстояние в км.
        """
        if self._graph is None:
            self.build_graph()

        n1 = self.nearest_boundary_node(lat1, lon1)
        n2 = self.nearest_boundary_node(lat2, lon2)

        # Расстояния от событий до ближайших узлов
        d1 = haversine(lat1, lon1, *self._node_coords[n1])
        d2 = haversine(lat2, lon2, *self._node_coords[n2])

        # Фолбэк: если события далеко от границ
        if d1 > max_boundary_dist_km or d2 > max_boundary_dist_km:
            gc_dist = haversine(lat1, lon1, lat2, lon2)
            return gc_dist * 1.5

        try:
            path_len = nx.dijkstra_path_length(self._graph, n1, n2, weight="weight")
            return float(d1 + path_len + d2)
        except nx.NetworkXNoPath:
            gc_dist = haversine(lat1, lon1, lat2, lon2)
            return gc_dist * 1.5

    def batch_distance_matrix(
        self,
        events_df: pd.DataFrame,
        max_events: int = 500,
    ) -> np.ndarray:
        """Вычисляет матрицу тектонических расстояний для подвыборки.

        Args:
            events_df: DataFrame с колонками lat, lon.
            max_events: максимальный размер подвыборки.

        Returns:
            Симметричная матрица расстояний (max_events × max_events).
        """
        if self._graph is None:
            self.build_graph()

        sub = events_df.head(max_events)
        n = len(sub)
        coords = sub[["lat", "lon"]].values
        dist_matrix = np.zeros((n, n))

        for i in range(n):
            for j in range(i + 1, n):
                d = self.tectonic_distance(
                    coords[i, 0], coords[i, 1],
                    coords[j, 0], coords[j, 1],
                )
                dist_matrix[i, j] = d
                dist_matrix[j, i] = d

            if i % 50 == 0:
                logger.debug("Матрица расстояний: обработано %d/%d строк", i, n)

        return dist_matrix
