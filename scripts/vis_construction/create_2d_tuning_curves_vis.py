
import h5py
import pynwb
import pynapple as nap
import remfile
from .TuningCurves2DView import TuningCurves2DView


def create_2d_tuning_curves_vis(url: str):
    # Lazy load NWB file
    file = remfile.File(url)
    with h5py.File(file, "r") as f:
        nwbfile = pynwb.NWBHDF5IO(file=f, mode="r").read()

        # Load the spatial series into a pynapple TsdFrame
        spatial_series = nwbfile.processing["behavior"]["Position"]["SpatialSeriesLED1"]
        position_over_time = nap.TsdFrame(
            d=spatial_series.data[:],
            t=spatial_series.timestamps[:],
            columns=["x", "y"],
        )

        # Load the unit spike times into a pynapple TsGroup
        unit_names = nwbfile.units["unit_name"][:]
        unit_spike_times = nwbfile.units["spike_times"][:]
        spike_times_group = nap.TsGroup(
            {i: unit_spike_times[i] for i in range(len(unit_names))}
        )

        # Compute 2D tuning curves
        num_bins = 30
        rate_maps, position_bins = nap.compute_2d_tuning_curves(
            spike_times_group,
            position_over_time,
            num_bins,
        )

        # Construct a tuning curves figurl view
        V = TuningCurves2DView(
            rate_maps=[rate_maps[i] for i in range(len(unit_names))],
            x_bin_positions=position_bins[0],
            y_bin_positions=position_bins[1],
            unit_ids=unit_names,
            unit_num_spikes=[len(spike_times_group[i]) for i in range(len(unit_names))],
        )
        return V
