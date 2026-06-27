"""Коррекция p-value на множественное тестирование для серий землетрясений.

При поиске глобальных серий каждая серия проверяется отдельным тестом.
При большом числе тестов возрастает вероятность ложных открытий.
Данный модуль предоставляет инструменты контроля уровня ошибок:
- Поправка Бонферрони (FWER).
- Метод Бенджамини-Хохберга (FDR).
- Оценка эффективного числа тестов (Meff) для коррелированных тестов.
"""

from __future__ import annotations

import logging

import numpy as np
import pandas as pd
from statsmodels.stats.multitest import multipletests

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Поправка Бонферрони
# ---------------------------------------------------------------------------

def apply_bonferroni(
    pvalues: np.ndarray,
    alpha: float = 0.01,
) -> np.ndarray:
    """Поправка Бонферрони на множественное тестирование.

    Скорректированное p-value = min(p * n, 1.0), где n — число тестов.
    Контролирует вероятность хотя бы одной ошибки I рода (FWER).

    Args:
        pvalues: массив сырых p-value.
        alpha: уровень значимости (используется только для логирования).

    Returns:
        Массив скорректированных p-value той же длины.
    """
    n = len(pvalues)
    if n == 0:
        return np.array([])
    adjusted = np.minimum(np.asarray(pvalues, dtype=float) * n, 1.0)
    n_sig = int(np.sum(adjusted < alpha))
    logger.info(
        "Бонферрони: %d тестов, %d значимых при α=%.3f", n, n_sig, alpha,
    )
    return adjusted


# ---------------------------------------------------------------------------
# Метод Бенджамини-Хохберга (FDR BH)
# ---------------------------------------------------------------------------

def apply_fdr_bh(
    pvalues: np.ndarray,
    alpha: float = 0.05,
) -> tuple[np.ndarray, np.ndarray]:
    """Метод Бенджамини-Хохберга (1995) для контроля доли ложных открытий.

    Контролирует FDR (False Discovery Rate) — ожидаемую долю ложных
    отклонений среди всех отклонений нулевой гипотезы.

    Args:
        pvalues: массив сырых p-value.
        alpha: целевой уровень FDR.

    Returns:
        Кортеж ``(reject_array, adjusted_pvalues)``:
        - ``reject_array``: булев массив, True = гипотеза отвергается.
        - ``adjusted_pvalues``: скорректированные p-value по BH.
    """
    pvalues = np.asarray(pvalues, dtype=float)
    if len(pvalues) == 0:
        return np.array([], dtype=bool), np.array([])

    reject, pvals_corrected, _, _ = multipletests(
        pvalues, alpha=alpha, method="fdr_bh",
    )
    n_sig = int(np.sum(reject))
    logger.info(
        "BH FDR: %d тестов, %d значимых при α=%.3f", len(pvalues), n_sig, alpha,
    )
    return reject, pvals_corrected


# ---------------------------------------------------------------------------
# FDR для словаря серий
# ---------------------------------------------------------------------------

def apply_bh_to_series(
    series_pvalues: dict[str, float],
    alpha: float = 0.05,
) -> pd.DataFrame:
    """Применяет FDR BH к словарю {series_id: pvalue}.

    Удобная обёртка для использования напрямую с результатами
    ``MonteCarloTester``.

    Args:
        series_pvalues: словарь ``{series_id: raw_pvalue}``.
        alpha: целевой уровень FDR.

    Returns:
        DataFrame с колонками:
        ``series_id``, ``raw_pvalue``, ``adjusted_pvalue``,
        ``reject_h0``, ``significant``.
    """
    if not series_pvalues:
        return pd.DataFrame(
            columns=["series_id", "raw_pvalue", "adjusted_pvalue", "reject_h0", "significant"]
        )

    ids = list(series_pvalues.keys())
    raw_pvals = np.array([series_pvalues[k] for k in ids], dtype=float)

    reject, adj_pvals = apply_fdr_bh(raw_pvals, alpha=alpha)

    result = pd.DataFrame({
        "series_id": ids,
        "raw_pvalue": raw_pvals,
        "adjusted_pvalue": adj_pvals,
        "reject_h0": reject,
        "significant": reject,
    })
    return result.sort_values("adjusted_pvalue").reset_index(drop=True)


# ---------------------------------------------------------------------------
# Эффективное число тестов (Meff)
# ---------------------------------------------------------------------------

def effective_number_of_tests(
    pvalues: np.ndarray,
    method: str = "meff",
) -> int:
    """Оценивает эффективное число независимых тестов.

    Используется когда тесты пространственно-временны́е окна
    перекрываются и тесты коррелированы.

    Метод ``'meff'`` (Li & Ji, 2005): Meff = количество эigenvalues
    матрицы корреляций, объясняющих 99.5% дисперсии.

    Args:
        pvalues: матрица p-value формы (n_tests, n_permutations) или
                 1D-массив p-value (в этом случае возвращается просто len).
        method: ``'meff'`` — метод Meff на основе PCA;
                ``'simple'`` — просто len(pvalues).

    Returns:
        Целое число — оценка Meff.
    """
    pvalues = np.asarray(pvalues, dtype=float)

    if pvalues.ndim == 1 or method == "simple":
        return int(len(pvalues))

    if method != "meff":
        raise ValueError(f"Неизвестный метод: {method!r}. Используйте 'meff' или 'simple'.")

    # pvalues: (n_tests, n_perms) — преобразуем в Z-scores для корреляции
    n_tests = pvalues.shape[0]
    if n_tests < 2:
        return 1

    # Преобразуем p-value в Z-scores (нормальная обратная CDF)
    from scipy.stats import norm
    clipped = np.clip(pvalues, 1e-10, 1 - 1e-10)
    z_scores = norm.ppf(1 - clipped)  # (n_tests, n_perms)

    # Матрица корреляций между тестами
    corr = np.corrcoef(z_scores)
    corr = np.nan_to_num(corr, nan=0.0)
    np.fill_diagonal(corr, 1.0)

    # Eigenvalues
    eigenvalues = np.linalg.eigvalsh(corr)
    eigenvalues = np.clip(eigenvalues, 0, None)[::-1]

    # Meff = число eigenvalues, объясняющих >= 99.5% дисперсии
    total = eigenvalues.sum()
    if total == 0:
        return n_tests
    cumulative = np.cumsum(eigenvalues) / total
    meff = int(np.searchsorted(cumulative, 0.995)) + 1
    meff = min(meff, n_tests)

    logger.info("Meff оценка: %d из %d тестов", meff, n_tests)
    return meff


# ---------------------------------------------------------------------------
# Метод Холма (Bonferroni-Holm)
# ---------------------------------------------------------------------------

def bonferroni_holm(
    pvalues: np.ndarray,
    alpha: float = 0.05,
) -> tuple[np.ndarray, np.ndarray]:
    """Метод Холма (Holm, 1979) — пошаговый контроль FWER.

    Более мощный чем простой Бонферрони, но также контролирует FWER
    (Family-Wise Error Rate).

    Процедура:
    1. Сортировать p(1) ≤ p(2) ≤ ... ≤ p(M).
    2. Для каждого i: критическое значение α_i = α / (M - i + 1).
    3. Отклонить H0_i если p(j) ≤ α_j для всех j ≤ i (пошаговое условие).
    4. Как только встретили p(i) > α_i — останавливаемся.

    Args:
        pvalues: массив сырых p-value.
        alpha: уровень значимости (FWER).

    Returns:
        Кортеж ``(reject_array, adjusted_pvalues)``:
        - ``reject_array``: булев массив (в исходном порядке).
        - ``adjusted_pvalues``: скорректированные p-value по Холму.
    """
    pvalues = np.asarray(pvalues, dtype=float)
    n = len(pvalues)
    if n == 0:
        return np.array([], dtype=bool), np.array([])

    order = np.argsort(pvalues)
    sorted_p = pvalues[order]

    # Скорректированные p-value: p_adj[i] = min(1, max_{j<=i}( (M-j+1)*p[j] ))
    adj = np.minimum(sorted_p * np.arange(n, 0, -1), 1.0)
    # Монотонное возрастание (условие пошаговости)
    adj = np.maximum.accumulate(adj)
    adj = np.clip(adj, 0.0, 1.0)

    reject_sorted = adj <= alpha
    # Пошаговая остановка: после первого не-отвержения — все последующие принимаются
    first_accept = np.where(~reject_sorted)[0]
    if len(first_accept) > 0:
        reject_sorted[first_accept[0]:] = False

    # Восстановить исходный порядок
    reject = np.empty(n, dtype=bool)
    adj_original = np.empty(n)
    reject[order] = reject_sorted
    adj_original[order] = adj

    n_sig = int(reject.sum())
    logger.info("Холм: %d тестов, %d значимых при α=%.3f", n, n_sig, alpha)
    return reject, adj_original


# ---------------------------------------------------------------------------
# Оценка эффективного числа тестов через скользящие корреляции
# ---------------------------------------------------------------------------

def compute_m_eff(
    pvalues: np.ndarray,
    window_size: int = 50,
) -> int:
    """Оценка эффективного числа независимых тестов (M_eff).

    Метод: скользящее окно корреляций p-values.
    Для перекрывающихся временных окон p-values коррелированы.
    M_eff ≈ M * (1 - mean_autocorrelation)

    Для слишком короткого массива или отсутствия автокорреляции
    возвращает len(pvalues).

    Args:
        pvalues: массив p-values (отсортированный по времени окна).
        window_size: размер окна для оценки автокорреляции (лаг 1).

    Returns:
        Целое число — оценка M_eff ∈ [1, len(pvalues)].
    """
    pvalues = np.asarray(pvalues, dtype=float)
    n = len(pvalues)
    if n <= 2:
        return n

    # Оценка автокорреляции лага 1 через скользящее окно
    autocorrs: list[float] = []
    step = max(1, window_size // 2)
    for start in range(0, n - window_size, step):
        chunk = pvalues[start: start + window_size]
        if np.std(chunk) < 1e-10:
            continue
        corr = float(np.corrcoef(chunk[:-1], chunk[1:])[0, 1])
        if np.isfinite(corr):
            autocorrs.append(abs(corr))

    if not autocorrs:
        return n

    mean_ac = float(np.mean(autocorrs))
    m_eff = max(1, int(round(n * (1.0 - mean_ac))))
    logger.info(
        "compute_m_eff: M=%d, mean_ac=%.3f → M_eff=%d", n, mean_ac, m_eff,
    )
    return m_eff


# ---------------------------------------------------------------------------
# Сводная таблица влияния коррекции
# ---------------------------------------------------------------------------

def summarize_correction_impact(
    series_ids: list[str],
    raw_pvalues: np.ndarray,
    method: str = "fdr_bh",
    alpha: float = 0.05,
) -> pd.DataFrame:
    """Сводная таблица влияния коррекции на множественное тестирование.

    Сравнивает результаты до и после поправки, классифицируя каждую серию.

    Args:
        series_ids: список идентификаторов серий.
        raw_pvalues: массив сырых p-value (в том же порядке).
        method: метод коррекции: ``'fdr_bh'``, ``'bonferroni'``, ``'holm'``.
        alpha: уровень значимости.

    Returns:
        DataFrame с колонками:
        ``series_id``, ``raw_pvalue``, ``adjusted_pvalue``,
        ``significant_raw``, ``significant_adjusted``, ``status``.

        Значения ``status``:
        - ``'survived'``: значимо до и после коррекции.
        - ``'removed_by_correction'``: значимо до, но не после коррекции.
        - ``'added_by_correction'``: незначимо до, но значимо после.
        - ``'not_significant'``: незначимо ни до, ни после.
    """
    raw_pvalues = np.asarray(raw_pvalues, dtype=float)
    n = len(raw_pvalues)

    if method == "fdr_bh":
        reject, adj_pvals = apply_fdr_bh(raw_pvalues, alpha=alpha)
    elif method == "bonferroni":
        adj_pvals = apply_bonferroni(raw_pvalues, alpha=alpha)
        reject = adj_pvals < alpha
    elif method == "holm":
        reject, adj_pvals = bonferroni_holm(raw_pvalues, alpha=alpha)
    else:
        raise ValueError(f"Неизвестный метод: {method!r}. Используйте 'fdr_bh', 'bonferroni' или 'holm'.")

    sig_raw = raw_pvalues < alpha
    sig_adj = reject.astype(bool)

    status = []
    for raw_ok, adj_ok in zip(sig_raw, sig_adj):
        if raw_ok and adj_ok:
            status.append("survived")
        elif raw_ok and not adj_ok:
            status.append("removed_by_correction")
        elif not raw_ok and adj_ok:
            status.append("added_by_correction")
        else:
            status.append("not_significant")

    result = pd.DataFrame({
        "series_id": series_ids,
        "raw_pvalue": raw_pvalues,
        "adjusted_pvalue": adj_pvals,
        "significant_raw": sig_raw,
        "significant_adjusted": sig_adj,
        "status": status,
    })

    n_survived = int((np.array(status) == "survived").sum())
    n_removed = int((np.array(status) == "removed_by_correction").sum())
    logger.info(
        "summarize_correction_impact (%s, α=%.3f): %d выжило, %d удалено",
        method, alpha, n_survived, n_removed,
    )
    return result.sort_values("raw_pvalue").reset_index(drop=True)
