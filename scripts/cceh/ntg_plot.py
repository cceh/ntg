# -*- encoding: utf-8 -*-

""" This module contains plot functions. """

from __future__ import print_function
from __future__ import unicode_literals

import numpy as np
import matplotlib.pyplot as plt
import matplotlib.colors as colors
import six


def mss_labels (hss, hsnrs):
    """Build ticks and labels for manuscript axis.

    Use one tick at the start of each range (papyri, maiuscles, ...) and then
    one every 5 mss.

    """

    hsnrs = np.array (hsnrs)

    range_ = -1
    c = 0
    ticks = []
    for n, hsnr in enumerate (hsnrs):
        i = hsnr // 100000
        if i > range_:
            ticks.append (n)
            range_ = i
            c = 0
            continue
        c += 1
        if (c % 5) == 0:
            ticks.append (n)

    labels = [hss[i] for i in ticks]
    return ticks, labels


def passages_labels (passages):
    """Build ticks and labels for passages axis.

    Use one tick every verse.

    """

    def group_by (s):
        return s[:3]

    def title (s):
        return s[1:3]

    group = None
    ticks = []
    labels = []

    for i, passage in enumerate (passages):
        g = group_by (passage)
        if g != group:
            ticks.append (i)
            labels.append (title (passage))
            group = g

    return ticks, labels


def colormap_bw ():
    # return colors.from_levels_and_colors ([0, 0.5, 1], ['white', 'black'])
    return (colors.LinearSegmentedColormap.from_list ('BW', ['white', 'black']),
            colors.Normalize (vmin = 0.0, vmax = 1.0))


def colormap_affinity ():
    return ('jet', # colors.LinearSegmentedColormap.from_list ('Affinity', ['white', 'blue']),
            colors.Normalize (vmin = 0.0, vmax = 1.0))


def heat_matrix (m, caption, ticks_labels_x, ticks_labels_y, colormap):
    """ Plot a heat map of the matrix. """

    plt.matshow (m, aspect = 'auto', cmap = colormap[0], norm = colormap[1])
    plt.colorbar ()

    plt.xticks (ticks_labels_x[0], ticks_labels_x[1], rotation='vertical')
    plt.yticks (ticks_labels_y[0], ticks_labels_y[1])
    axes = plt.gca ()
    axes.tick_params (direction = 'out', pad = 5)

    plt.title (caption)
    plt.show ()
