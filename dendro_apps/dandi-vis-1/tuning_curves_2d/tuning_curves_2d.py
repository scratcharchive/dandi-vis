#!/usr/bin/env python


from dendro.sdk import ProcessorBase, InputFile, OutputFile
from dendro.sdk import BaseModel, Field


class TuningCurves2DContext(BaseModel):
    input: InputFile = Field(description="Input NWB file")
    output: OutputFile = Field(description="Output .nh5 file")
    spatial_series_path: str = Field(
        description="Path to spatial series within NWB file, e.g. '/processing/behavior/Position/SpatialSeriesLED1'"
    )
    units_path: str = Field(
        default="/units", description="Path to units within NWB file, default: '/units'"
    )
    num_bins: int = Field(
        description="Number of bins (in one dimension) for tuning curves"
    )


class TuningCurves2DProcessor(ProcessorBase):
    name = "dandi-vis-1.tuning_curves_2d"
    description = "Create 2D tuning curves from an NWB file using Pynapple"
    label = "dandi-vis-1.tuning_curves_2d"
    tags = ["pynapple", "nwb"]
    attributes = {"wip": True}

    @staticmethod
    def run(context: TuningCurves2DContext):
        import numpy as np
        import pynwb
        import pynapple as nap
        import h5py
        from nh5 import h5_to_nh5
        from load_nwb_object import load_nwb_object

        input_file = context.input.get_file()
        input_nwb = pynwb.NWBHDF5IO(file=h5py.File(input_file, "r"), mode="r").read()

        num_bins = context.num_bins
        spatial_series_path = context.spatial_series_path
        units_path = context.units_path

        # Load the spatial series into a pynapple TsdFrame
        spatial_series = load_nwb_object(input_nwb, spatial_series_path)
        position_over_time = nap.TsdFrame(
            d=spatial_series.data[:],
            t=spatial_series.timestamps[:],
            columns=["x", "y"],
        )

        # Load the unit spike times into a pynapple TsGroup
        units = load_nwb_object(input_nwb, units_path)
        unit_names = units["unit_name"][:]
        unit_spike_times = units["spike_times"][:]
        spike_times_group = nap.TsGroup(
            {i: unit_spike_times[i] for i in range(len(unit_names))}
        )

        # Compute 2D tuning curves
        rate_maps, position_bins = nap.compute_2d_tuning_curves(
            spike_times_group,
            position_over_time,
            num_bins,
        )

        rate_maps_concat = np.zeros(
            (len(unit_names), num_bins, num_bins), dtype=np.float32
        )
        for i in range(len(unit_names)):
            rate_maps_concat[i, :, :] = rate_maps[i].astype(np.float32)
        x_bin_positions = position_bins[0].astype(np.float32)
        y_bin_positions = position_bins[1].astype(np.float32)

        output_h5_fname = "output.h5"
        with h5py.File(output_h5_fname, "w") as f:
            f.create_dataset("rate_maps", data=rate_maps_concat)
            f.create_dataset("x_bin_positions", data=x_bin_positions)
            f.create_dataset("y_bin_positions", data=y_bin_positions)
            f.attrs["unit_ids"] = [x for x in unit_names]
            f.attrs["type"] = "tuning_curves_2d"
            f.attrs["format_version"] = 1

        output_nh5_fname = "output.nh5"
        h5_to_nh5(output_h5_fname, output_nh5_fname)

        context.output.upload(output_nh5_fname)
