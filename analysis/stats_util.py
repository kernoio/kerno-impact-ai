"""Shared statistics for the raw-data scripts (same methods as 03_analysis.py)."""
import math
import random
import statistics as st

B = 10000


def sign_test(k, n):
    """Exact two-sided binomial sign test, H0 p=0.5."""
    if n == 0:
        return None
    tail = sum(math.comb(n, i) for i in range(0, min(k, n - k) + 1)) / 2 ** n
    return min(1.0, 2 * tail)


def boot_median_ci(xs, seed):
    if len(xs) < 3:
        return (None, None)
    rnd = random.Random(seed)
    meds = sorted(st.median(rnd.choices(xs, k=len(xs))) for _ in range(B))
    return (meds[int(0.025 * B)], meds[int(0.975 * B) - 1])


def quartiles(xs):
    if len(xs) < 2:
        return (None, None)
    q = st.quantiles(xs, n=4, method="inclusive")
    return (q[0], q[2])


def rank(xs):
    order = sorted(range(len(xs)), key=lambda i: xs[i])
    r = [0.0] * len(xs)
    i = 0
    while i < len(xs):
        j = i
        while j + 1 < len(xs) and xs[order[j + 1]] == xs[order[i]]:
            j += 1
        for k in range(i, j + 1):
            r[order[k]] = (i + j) / 2 + 1
        i = j + 1
    return r


def spearman(x, y):
    rx, ry = rank(x), rank(y)
    mx, my = st.mean(rx), st.mean(ry)
    num = sum((a - mx) * (b - my) for a, b in zip(rx, ry))
    den = math.sqrt(sum((a - mx) ** 2 for a in rx) * sum((b - my) ** 2 for b in ry))
    return num / den if den else 0.0


def spearman_perm(x, y, seed):
    rho = spearman(x, y)
    rnd = random.Random(seed)
    yy = list(y)
    hits = sum(abs(spearman(x, (rnd.shuffle(yy), yy)[1])) >= abs(rho) - 1e-12 for _ in range(B))
    return rho, (hits + 1) / (B + 1)


def describe(changes, seed):
    """Distribution of per-repo % changes: counts, median, IQR, bootstrap CI, sign test."""
    xs = [c for c in changes if c is not None]
    up = sum(c > 0 for c in xs)
    down = sum(c < 0 for c in xs)
    lo, hi = boot_median_ci(xs, seed)
    q1, q3 = quartiles(xs)
    return dict(n=len(xs), rose=up, fell=down, median=st.median(xs) if xs else None, q1=q1, q3=q3,
                mean=st.mean(xs) if xs else None, ci_low=lo, ci_high=hi, sign_p=sign_test(up, up + down))
