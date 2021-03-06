import pandas as pd
import numpy as np
import sys


def read_bed(filename, sort=False, usecols=[0, 1, 2], *args, **kwargs):
    """Read chromo,start,end from BED file without formatting chromo."""
    d = pd.read_table(filename, header=None, usecols=usecols, *args, **kwargs)
    d.columns = range(d.shape[1])
    d.rename(columns={0: 'chromo', 1: 'start', 2: 'end'}, inplace=True)
    if sort:
        d.sort(['chromo', 'start', 'end'], inplace=True)
    return d


def in_which(x, ys, ye):
    """Returns for positions x[i] index j, s.t. ys[j] <= x[i] <= ye[j] or -1.
       Intervals must be non-overlapping!

    Parameters
    ----------
    x : list of positions
    ys: list with start of interval sorted in ascending order
    ye: list with end of interval

    Returns
    -------
    numpy array of same length than x with index or -1
    """

    n = len(ys)
    m = len(x)
    rv = np.empty(m, dtype=np.int)
    rv.fill(-1)
    i = 0
    j = 0
    while i < n and j < m:
        while j < m and x[j] <= ye[i]:
            if x[j] >= ys[i]:
                rv[j] = i
            j += 1
        i += 1
    return rv


def is_in(pos, start, end):
    return in_which(pos, start, end) >= 0


def distance(pos, start, end):
    m = len(start)
    n = len(pos)
    i = 0
    j = 0
    end_prev = -10**7
    dist = np.zeros(n)
    while i < m and j < n:
        while j < n and pos[j] <= end[i]:
            if pos[j] < start[i]:
                dist[j] = min(pos[j] - end_prev, start[i] - pos[j])
            j += 1
        end_prev = end[i]
        i += 1
    dist[j:] = pos[j:] - end_prev
    assert np.all(dist >= 0)
    return dist


def join_overlapping(s, e):
    """Transforms a list of possible overlapping intervals into
    non-overlapping intervals.

    Parameters
    ----------
    s : list with start of interval sorted in ascending order
    e : list with end of interval

    Returns
    -------
    Tuple (s, e) of non-overlapping intervals
    """
    rs = []
    re = []
    n = len(s)
    if n == 0:
        return (rs, re)
    l = s[0]
    r = e[0]
    for i in range(1, n):
        if s[i] > r:
            rs.append(l)
            re.append(r)
            l = s[i]
            r = e[i]
        else:
            r = max(r, e[i])
    rs.append(l)
    re.append(r)
    return (rs, re)


def join_overlapping_frame(d):
    d = d.sort(['chromo', 'start', 'end'])
    e = []
    for chromo in d.chromo.unique():
        dc = d.loc[d.chromo == chromo]
        start, end = join_overlapping(dc.start.values, dc.end.values)
        ec = pd.DataFrame(dict(chromo=chromo, start=start, end=end))
        e.append(ec)
    e = pd.concat(e)
    e = e.loc[:, ['chromo', 'start', 'end']]
    return e


def group_overlapping(s, e):
    """Assigns group index to intervals. Overlapping intervals will be assigned
       to the same group.

    Parameters
    ----------
    s : list with start of interval sorted in ascending order
    e : list with end of interval

    Returns
    -------
    int array of length len(s) with group indices
    """
    n = len(s)
    group = np.zeros(n, dtype='int32')
    if n == 0:
        return group
    idx = 0
    l = s[0]
    r = e[0]
    for i in range(1, n):
        if s[i] > r:
            idx += 1
            r = e[i]
        else:
            r = max(r, e[i])
        group[i] = idx
    return group


def extend_len(start, end, min_len, min_pos=1):
    delta = np.maximum(0, min_len - (end - start + 1))
    ext = np.floor(0.5 * delta).astype(np.int)
    start_ext = np.maximum(min_pos, start - ext)
    end_ext = end + np.maximum(0, (min_len - (end - start_ext + 1)))
    assert np.all(min_len <= (end_ext - start_ext + 1))
    return (start_ext, end_ext)


def extend_len_frame(d, min_len):
    start, end = extend_len(d.start.values, d.end.values, min_len)
    e = d.copy()
    e['start'] = start
    e['end'] = end
    return e
