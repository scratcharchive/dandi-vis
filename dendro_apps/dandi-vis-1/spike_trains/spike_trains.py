#!/usr/bin/env python


from typing import Optional
from dendro.sdk import ProcessorBase, InputFile, OutputFile
from dendro.sdk import BaseModel, Field


class SpikeTrainsContext(BaseModel):
    input: InputFile = Field(description="Input NWB file")
    output: OutputFile = Field(description="Output .nh5 file")
    units_path: str = Field(
        default="/units", description="Path to units within NWB file, default: '/units'"
    )
    sampling_frequency: Optional[float] = Field(
        default=None, description="Override the sampling frequency of the recording"
    )


class SpikeTrainsProcessor(ProcessorBase):
    name = "dandi-vis-1.spike_trains"
    description = "Create spike trains .nh5 file from an NWB file"
    label = "dandi-vis-1.spike_trains"
    tags = ["pynapple", "nwb"]
    attributes = {"wip": True}

    @staticmethod
    def run(context: SpikeTrainsContext):
        import numpy as np
        from nh5 import h5_to_nh5
        import h5py

        # with remfile support
        # and support for units_path
        from .NwbExtractors import NwbSortingExtractor

        input_file_url = context.input.get_url()

        units_path = context.units_path
        sampling_frequency = context.sampling_frequency

        # Load the unit spike times into a pynapple TsGroup
        sorting = NwbSortingExtractor(
            input_file_url,
            stream_mode="remfile",
            units_path=units_path,
            sampling_frequency=sampling_frequency,
        )

        unit_ids = [unit_id for unit_id in sorting.get_unit_ids()]
        total_num_spikes = 0
        max_time = -np.inf
        for unit_id in unit_ids:
            st = sorting.get_unit_spike_train(unit_id)
            total_num_spikes += len(st)
            if len(st) > 0:
                max_time = max(max_time, np.max(st) / sorting.get_sampling_frequency())
        num_spikes_per_chunk = 500000
        approx_num_chunks = int(np.ceil(total_num_spikes / num_spikes_per_chunk))
        total_duration_sec = max_time  # we assume the start time is 0
        approx_duration_per_chunk_sec = total_duration_sec / approx_num_chunks
        duration_per_chunk_sec_options = [
            10,
            100,
            200,
            500,
            1000,
            2000,
            5000,
            10000,
            20000,
            50000,
            100000,
        ]
        for duration_per_chunk_sec in duration_per_chunk_sec_options:
            if approx_duration_per_chunk_sec < duration_per_chunk_sec:
                break
        num_chunks = int(np.ceil(total_duration_sec / duration_per_chunk_sec))
        print(f'Using {num_chunks} chunks of duration {duration_per_chunk_sec} sec')
        chunks = []
        for i in range(num_chunks):
            start_time = i * duration_per_chunk_sec
            end_time = min((i + 1) * duration_per_chunk_sec, total_duration_sec)
            chunks.append({"start": start_time, "end": end_time})

        output_h5_fname = "output.h5"
        with h5py.File(output_h5_fname, "w") as f:
            f.attrs["type"] = "spike_trains"
            f.attrs["format_version"] = 1
            f.attrs["unit_ids"] = unit_ids
            f.attrs["chunks"] = chunks
            f.attrs["sampling_frequency"] = sorting.get_sampling_frequency()
            f.attrs["total_duration_sec"] = total_duration_sec
            f.attrs["total_num_spikes"] = total_num_spikes
            for i in range(len(chunks)):
                start_time = chunks[i]["start"]
                end_time = chunks[i]["end"]
                start_frame = int(start_time * sampling_frequency)
                end_frame = int(end_time * sampling_frequency)
                chunk_spike_trains = [
                    (
                        sorting.get_unit_spike_train(
                            unit_id, start_frame=start_frame, end_frame=end_frame
                        )
                        / sorting.get_sampling_frequency()
                        - start_time
                    ).astype(np.float32)
                    for unit_id in unit_ids
                ]
                if len(chunk_spike_trains) > 0:
                    spike_times = np.concatenate(chunk_spike_trains)
                else:
                    spike_times = np.array([], dtype=np.float32)
                spike_times_index = []
                ind = 0
                for i in range(len(chunk_spike_trains)):
                    ind += len(chunk_spike_trains[i])
                    spike_times_index.append(ind)
                spike_times_index = np.array(spike_times_index, dtype=np.int32)
                f.create_dataset(f"/chunk_{i}/spike_times", data=spike_times)
                f.create_dataset(
                    f"/chunk_{i}/spike_times_index", data=spike_times_index
                )
        output_nh5_fname = "output.nh5"
        h5_to_nh5(output_h5_fname, output_nh5_fname)
        context.output.upload(output_nh5_fname)
