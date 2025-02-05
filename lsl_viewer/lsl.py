import pylsl
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.gridspec import GridSpec
from matplotlib.widgets import CheckButtons, Slider
import time
from collections import deque

# Parameters
WINDOW_DURATION = 10  # X-axis fixed from 0 to 10 seconds
UPDATE_INTERVAL = 0.2  # Update every 200ms
SMOOTHING_WINDOW = 5  # Smoothing window size
VISIBLE_CHECKBOXES = 5  # Number of checkboxes visible at once

# Discover available LSL streams
streams = pylsl.resolve_streams()
inlets = []
sample_rates = []
channel_counts = []

for stream in streams:
    inlet = pylsl.StreamInlet(stream)
    sample_rate = inlet.info().nominal_srate()
    channel_count = inlet.info().channel_count()
    
    if sample_rate <= 0:
        sample_rate = 100  # Default to 100 Hz if unknown

    inlets.append((inlet, stream))
    sample_rates.append(sample_rate)
    channel_counts.append(channel_count)

# Initialize data buffers
data_buffers = []
time_buffers = []
for sr, channels in zip(sample_rates, channel_counts):
    num_samples = int(WINDOW_DURATION * sr)
    data_buffers.append([deque([np.nan] * num_samples, maxlen=num_samples) for _ in range(channels)])
    time_buffers.append(deque(np.linspace(-WINDOW_DURATION, 0, num_samples), maxlen=num_samples))

# Set up Matplotlib with compact left/right panels
num_streams = len(inlets)
fig = plt.figure(figsize=(14, max(3, 2 * num_streams)))  # Adjusted for better layout
gs = GridSpec(num_streams, 2, width_ratios=[1, 3], wspace=0.2, hspace=0.5)  

axes = []
check_buttons = []
channel_visibility = [[True] * ch for ch in channel_counts]
checkbox_axes = []
scroll_sliders = []

# Function to smooth data
def smooth_data(data, window=SMOOTHING_WINDOW):
    if len(data) < window:
        return data  # Not enough data to smooth
    return np.convolve(data, np.ones(window) / window, mode='same')

# Function to update checkboxes based on slider position
def update_checkboxes(val, idx):
    """ Update checkboxes dynamically when slider moves """
    start = int(val)
    end = min(start + VISIBLE_CHECKBOXES, channel_counts[idx])

    ax_check = checkbox_axes[idx]
    ax_check.clear()
    ax_check.set_title(f"{inlets[idx][1].name()}", fontsize=10, fontweight="bold", pad=3)
    ax_check.axis("off")

    labels = [f"Ch {ch+1}" for ch in range(start, end)]
    visibility = channel_visibility[idx][start:end]

    check = CheckButtons(ax_check, labels, visibility)

    def toggle_channels(label, idx=idx, start=start):
        ch_idx = start + int(label.split(" ")[1]) - 1
        channel_visibility[idx][ch_idx] = not channel_visibility[idx][ch_idx]

    check.on_clicked(toggle_channels)
    check_buttons[idx] = check  # Update reference

    plt.draw()

# Left panel for checkboxes with properly placed scrolling, right panel for plots
for idx, (inlet, stream) in enumerate(inlets):
    # Left panel (checkboxes)
    ax_check = fig.add_subplot(gs[idx, 0])
    ax_check.set_title(f"{stream.name()}", fontsize=10, fontweight="bold", pad=3)
    ax_check.axis("off")

    checkbox_axes.append(ax_check)

    labels = [f"Ch {ch+1}" for ch in range(min(VISIBLE_CHECKBOXES, channel_counts[idx]))]
    visibility = channel_visibility[idx][:VISIBLE_CHECKBOXES]

    check = CheckButtons(ax_check, labels, visibility)
    check_buttons.append(check)

    def toggle_channels(label, idx=idx):
        ch_idx = int(label.split(" ")[1]) - 1  # Extract channel number
        channel_visibility[idx][ch_idx] = not channel_visibility[idx][ch_idx]

    check.on_clicked(toggle_channels)

    # 🟢 Dynamically adjust scrollbar height
    if channel_counts[idx] > VISIBLE_CHECKBOXES:
        checkbox_height = 0.03 * VISIBLE_CHECKBOXES  # Each checkbox takes ~0.03 in height
        total_streams = len(inlets)
        slider_bottom = 1.03 - ((idx + 1) / total_streams) * 0.9  # Dynamically adjust Y position

        ax_slider = fig.add_axes([0.12, slider_bottom, 0.02, checkbox_height])  # Auto-fit height
        slider = Slider(ax_slider, '', 0, channel_counts[idx] - VISIBLE_CHECKBOXES, valinit=1, valstep=1, orientation="vertical")
        slider.on_changed(lambda val, idx=idx: update_checkboxes(val, idx))
        scroll_sliders.append(slider)

    # Right panel (plots)
    ax_plot = fig.add_subplot(gs[idx, 1])
    axes.append(ax_plot)

start_time = time.time()

# 🔄 Real-time plotting loop
while True:
    current_time = time.time() - start_time  # Fix incorrect time initialization

    for idx, (inlet, stream) in enumerate(inlets):
        sample, timestamp = inlet.pull_sample(timeout=0.1)

        if sample:
            for ch in range(channel_counts[idx]):
                data_buffers[idx][ch].append(sample[ch])

            time_buffers[idx].append(current_time)

    # Update plots smoothly
    for idx, (buffers, time_buffer, (inlet, stream)) in enumerate(zip(data_buffers, time_buffers, inlets)):
        axes[idx].cla()

        plotted_channels = 0
        for ch in range(channel_counts[idx]):
            if channel_visibility[idx][ch]:
                smoothed_data = smooth_data(list(buffers[ch]))
                axes[idx].plot(time_buffer, smoothed_data, label=f"Ch {ch+1}", linewidth=1.2, alpha=0.7)
                plotted_channels += 1

        axes[idx].set_title(f"{stream.name()} ({stream.type()})", fontsize=9, pad=2)
        axes[idx].set_xlabel("Time (s)", fontsize=8)
        axes[idx].set_ylabel("Value", fontsize=8)
        axes[idx].set_xlim(current_time - WINDOW_DURATION, current_time)
        axes[idx].tick_params(axis="both", labelsize=7)

        # 🌟 Adaptive legend placement (horizontal & compact)
        ncols = max(2, min(5, plotted_channels // 10))  # Adjust columns dynamically
        axes[idx].legend(fontsize=4, loc="upper left", bbox_to_anchor=(-0.0, 1.0), frameon=False, ncol=16)

    fig.tight_layout(pad=1.1)  # Adjust padding dynamically
    plt.pause(UPDATE_INTERVAL)
