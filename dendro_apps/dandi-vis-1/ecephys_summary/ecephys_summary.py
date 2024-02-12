#!/usr/bin/env python

from dendro.sdk import ProcessorBase, InputFile, OutputFile
from dendro.sdk import BaseModel, Field
import numpy as np


class EcephysSummaryContext(BaseModel):
    input: InputFile = Field(description="Input recording as SI .json file")
    output: OutputFile = Field(description="Output .nh5 file")


class EcephysSummaryProcessor(ProcessorBase):
    name = "dandi-vis-1.ecephys_summary"
    description = "Create ecephys summary .nh5 file from an NWB file"
    label = "dandi-vis-1.ecephys_summary"
    tags = ["nwb", "ecephys"]
    attributes = {"wip": True}

    @staticmethod
    def run(context: EcephysSummaryContext):
        import os
        import sys
        import h5py
        import spikeinterface as si
        from nh5 import h5_to_nh5

        # we need for nwbdendroextractors module to be discoverable
        thisdir = os.path.dirname(os.path.realpath(__file__))
        sys.path.append(thisdir)

        context.input.download('recording.json')

        print('Loading recording...')
        recording = si.load_extractor('recording.json')
        assert isinstance(recording, si.BaseRecording), "Recording is not a BaseRecording"

        num_frames = recording.get_num_frames()
        bin_size_sec = 1 / 5
        bin_size_frames = int(bin_size_sec * recording.get_sampling_frequency())
        num_bins = int(num_frames / bin_size_frames)
        M = int(recording.get_num_channels())

        print('Creating output .h5 file...')
        with h5py.File("output.h5", "w") as f:
            f.attrs["type"] = "ecephys_summary"
            f.attrs["format_version"] = 1
            f.attrs["num_frames"] = num_frames
            f.attrs["sampling_frequency"] = float(recording.get_sampling_frequency())
            f.attrs["num_channels"] = recording.get_num_channels()
            f.attrs["channel_ids"] = [id for id in recording.get_channel_ids()]
            f.create_dataset("channel_locations", data=recording.get_channel_locations())
            p_min = f.create_dataset("/binned_arrays/min", data=np.zeros((num_bins, M), dtype=np.int16))
            p_max = f.create_dataset("/binned_arrays/max", data=np.zeros((num_bins, M), dtype=np.int16))
            for p in [p_min, p_max]:
                p.attrs["bin_size_sec"] = bin_size_sec
                p.attrs["bin_size_frames"] = bin_size_frames
                p.attrs["num_bins"] = num_bins
            batches = []
            num_bins_per_batch = 1000
            i = 0
            while i < num_bins:
                bin_start = i
                bin_end = min(i + num_bins_per_batch, num_bins)
                batches.append({'bin_start': bin_start, 'bin_end': bin_end})
                i += num_bins_per_batch
            for ib in range(len(batches)):
                print(f'Processing batch {ib + 1} of {len(batches)}')
                bin_start = batches[ib]['bin_start']
                bin_end = batches[ib]['bin_end']
                num_bins_in_batch = bin_end - bin_start
                print(f"Processing batch {ib} of {len(batches)}")
                X = recording.get_traces(start_frame=bin_start * bin_size_frames, end_frame=bin_end * bin_size_frames)
                X_reshaped = X.reshape((num_bins_in_batch, bin_size_frames, M)).astype(np.int16)
                p_min[bin_start:bin_end, :] = np.min(X_reshaped, axis=1)
                p_max[bin_start:bin_end, :] = np.max(X_reshaped, axis=1)

        print('Converting .h5 to .nh5...')
        h5_to_nh5("output.h5", "output.nh5")
        print('Uploading .nh5...')
        context.output.upload("output.nh5")
