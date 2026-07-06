#!/usr/bin/env python3

import numpy as np
import matplotlib.pyplot as plt
from matplotlib.widgets import Slider


# -----------------------------------------------------------------------------
# Defaults from firmware
# -----------------------------------------------------------------------------

EVENT_THRESH_GRAMS = 50.0

EWMA_MASS_ALPHA_MIN = 0.02
EWMA_MASS_ALPHA_MAX = 0.7

# Logistic curve parameters
EWMA_MASS_ALPHA_MIDPOINT_GRAMS = 50.0
EWMA_MASS_ALPHA_STEEPNESS = 0.15


# -----------------------------------------------------------------------------
# Filter math
# -----------------------------------------------------------------------------

def compute_alpha(
    error,
    alpha_min,
    alpha_max,
    midpoint,
    steepness,
):
    """
    Logistic alpha curve.

    midpoint:
        Error where alpha is halfway between alpha_min and alpha_max.

    steepness:
        Controls how rapidly alpha transitions from smoothing mode
        to tracking mode.
    """

    return alpha_min + (
        alpha_max - alpha_min
    ) / (
        1.0 + np.exp(
            -steepness * (error - midpoint)
        )
    )


def effective_window(alpha):
    """
    Approximate EWMA averaging window.

    alpha = 0.02 -> ~50 samples
    alpha = 0.10 -> ~10 samples
    alpha = 0.50 -> ~2 samples
    """

    return 1.0 / alpha


# -----------------------------------------------------------------------------
# Figure
# -----------------------------------------------------------------------------

fig, (ax_alpha, ax_window) = plt.subplots(
    2,
    1,
    figsize=(10, 8),
)

plt.subplots_adjust(
    left=0.10,
    bottom=0.42,
)

errors = np.linspace(
    0.0,
    200.0,
    2000,
)

alpha = compute_alpha(
    errors,
    EWMA_MASS_ALPHA_MIN,
    EWMA_MASS_ALPHA_MAX,
    EWMA_MASS_ALPHA_MIDPOINT_GRAMS,
    EWMA_MASS_ALPHA_STEEPNESS,
)

(line_alpha,) = ax_alpha.plot(
    errors,
    alpha,
)

(event_line_alpha,) = ax_alpha.plot(
    [EVENT_THRESH_GRAMS, EVENT_THRESH_GRAMS],
    [0, 1],
    "--",
    label="EVENT_THRESH",
)

ax_alpha.set_title(
    "AEWMA Logistic Alpha"
)
ax_alpha.set_xlabel("Error (g)")
ax_alpha.set_ylabel("Alpha")
ax_alpha.grid(True)
ax_alpha.set_ylim(0, 1)
ax_alpha.legend()

window = effective_window(alpha)

(line_window,) = ax_window.plot(
    errors,
    window,
)

(event_line_window,) = ax_window.plot(
    [EVENT_THRESH_GRAMS, EVENT_THRESH_GRAMS],
    [0, np.max(window)],
    "--",
)

ax_window.set_title("Effective Memory in Samples")
ax_window.set_xlabel("Error (g)")
ax_window.set_ylabel("Samples")
ax_window.grid(True)
ax_window.set_ylim(0, 60)

# -----------------------------------------------------------------------------
# Sliders
# -----------------------------------------------------------------------------

ax_event = plt.axes([0.15, 0.32, 0.70, 0.03])

ax_alpha_min = plt.axes([0.15, 0.27, 0.70, 0.03])

ax_alpha_max = plt.axes([0.15, 0.22, 0.70, 0.03])

ax_midpoint = plt.axes([0.15, 0.17, 0.70, 0.03])

ax_steepness = plt.axes([0.15, 0.12, 0.70, 0.03])

s_event = Slider(
    ax_event,
    "EVENT_THRESH",
    1,
    200,
    valinit=EVENT_THRESH_GRAMS,
)

s_alpha_min = Slider(
    ax_alpha_min,
    "ALPHA_MIN",
    0.001,
    0.2,
    valinit=EWMA_MASS_ALPHA_MIN,
)

s_alpha_max = Slider(
    ax_alpha_max,
    "ALPHA_MAX",
    0.05,
    1.0,
    valinit=EWMA_MASS_ALPHA_MAX,
)

s_midpoint = Slider(
    ax_midpoint,
    "MIDPOINT",
    1,
    200,
    valinit=EWMA_MASS_ALPHA_MIDPOINT_GRAMS,
)

s_steepness = Slider(
    ax_steepness,
    "STEEPNESS",
    0.01,
    1.0,
    valinit=EWMA_MASS_ALPHA_STEEPNESS,
)

# -----------------------------------------------------------------------------
# Update callback
# -----------------------------------------------------------------------------

def update(_):

    alpha = compute_alpha(
        errors,
        s_alpha_min.val,
        s_alpha_max.val,
        s_midpoint.val,
        s_steepness.val,
    )

    line_alpha.set_ydata(alpha)

    window = effective_window(alpha)
    line_window.set_ydata(window)

    event_line_alpha.set_xdata(
        [s_event.val, s_event.val]
    )

    event_line_window.set_xdata(
        [s_event.val, s_event.val]
    )

    fig.canvas.draw_idle()


s_event.on_changed(update)
s_alpha_min.on_changed(update)
s_alpha_max.on_changed(update)
s_midpoint.on_changed(update)
s_steepness.on_changed(update)

plt.show()