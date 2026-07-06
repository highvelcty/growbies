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
EWMA_MASS_ALPHA_THRESH_GRAMS = 25.0


# -----------------------------------------------------------------------------
# Filter math
# -----------------------------------------------------------------------------

def compute_alpha(error, alpha_min, alpha_max, alpha_threshold):
    alpha = np.sqrt(error / alpha_threshold)

    alpha = np.maximum(alpha, alpha_min)
    alpha = np.minimum(alpha, alpha_max)

    return alpha


def effective_window(alpha):
    """
    Approximate EWMA averaging window.

    alpha = 0.02 -> ~50 samples
    alpha = 0.1  -> ~10 samples
    alpha = 0.5  -> ~2 samples
    """
    return 1.0 / alpha


# -----------------------------------------------------------------------------
# Figure
# -----------------------------------------------------------------------------

fig, (ax_alpha, ax_window) = plt.subplots(2, 1, figsize=(10, 8))
plt.subplots_adjust(left=0.10, bottom=0.35)

errors = np.linspace(0.0, 100.0, 2000)

alpha = compute_alpha(
    errors,
    EWMA_MASS_ALPHA_MIN,
    EWMA_MASS_ALPHA_MAX,
    EWMA_MASS_ALPHA_THRESH_GRAMS,
)

(line_alpha,) = ax_alpha.plot(errors, alpha)
(event_line_alpha,) = ax_alpha.plot(
    [EVENT_THRESH_GRAMS, EVENT_THRESH_GRAMS],
    [0, 1],
    "--",
    label="EVENT_THRESH",
)

ax_alpha.set_title("AEWMA Alpha vs Error")
ax_alpha.set_xlabel("Error (g)")
ax_alpha.set_ylabel("Alpha")
ax_alpha.grid(True)
ax_alpha.set_ylim(0, 1)
ax_alpha.legend()

window = effective_window(alpha)

(line_window,) = ax_window.plot(errors, window)
(event_line_window,) = ax_window.plot(
    [EVENT_THRESH_GRAMS, EVENT_THRESH_GRAMS],
    [0, np.max(window)],
    "--",
)

ax_window.set_title("Approximate EWMA Window Length")
ax_window.set_xlabel("Error (g)")
ax_window.set_ylabel("Samples")
ax_window.grid(True)
ax_window.set_ylim(0, 60)

# -----------------------------------------------------------------------------
# Sliders
# -----------------------------------------------------------------------------

ax_event = plt.axes([0.15, 0.25, 0.70, 0.03])
ax_alpha_min = plt.axes([0.15, 0.20, 0.70, 0.03])
ax_alpha_max = plt.axes([0.15, 0.15, 0.70, 0.03])
ax_alpha_thresh = plt.axes([0.15, 0.10, 0.70, 0.03])

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

s_alpha_thresh = Slider(
    ax_alpha_thresh,
    "ALPHA_THRESH",
    1,
    200,
    valinit=EWMA_MASS_ALPHA_THRESH_GRAMS,
)


# -----------------------------------------------------------------------------
# Update callback
# -----------------------------------------------------------------------------

def update(_):

    alpha = compute_alpha(
        errors,
        s_alpha_min.val,
        s_alpha_max.val,
        s_alpha_thresh.val,
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
s_alpha_thresh.on_changed(update)

plt.show()