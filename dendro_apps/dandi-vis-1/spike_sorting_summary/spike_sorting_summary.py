#!/usr/bin/env python


from typing import Optional
from dendro.sdk import ProcessorBase, InputFile, OutputFile
from dendro.sdk import BaseModel, Field
from typing import TYPE_CHECKING
import numpy as np

if TYPE_CHECKING:
    import spikeinterface as si
    import h5py


class SpikeSortingSummaryContext(BaseModel):
    input: InputFile = Field(description="Input NWB file")
    output: OutputFile = Field(description="Output .nh5 file")
    units_path: str = Field(
        default="/units", description="Path to units within NWB file, default: '/units'"
    )
    sampling_frequency: Optional[float] = Field(
        default=None, description="Override the sampling frequency of the recording"
    )


class SpikeSortingSummaryProcessor(ProcessorBase):
    name = "dandi-vis-1.spike_sorting_summary"
    description = "Create spike sorting summary .nh5 file from an NWB file"
    label = "dandi-vis-1.spike_sorting_summary"
    tags = ["nwb", "spike sorting"]
    attributes = {"wip": True}

    @staticmethod
    def run(context: SpikeSortingSummaryContext):
        import numpy as np
        from nh5 import h5_to_nh5
        import h5py

        # with remfile support
        # and support for units_path
        # and try/catch for setting properties
        from .NwbExtractors import NwbSortingExtractor

        input_file_url = context.input.get_url()

        units_path = context.units_path
        sampling_frequency = context.sampling_frequency

        # Load the spike sorting
        sorting = NwbSortingExtractor(
            input_file_url,
            stream_mode="remfile",
            units_path=units_path,
            sampling_frequency=sampling_frequency,
        )

        if sampling_frequency is None:
            sampling_frequency = sorting.get_sampling_frequency()

        unit_ids = [unit_id for unit_id in sorting.get_unit_ids()]
        total_num_spikes = 0
        max_time = -np.inf
        spike_counts = []
        for unit_id in unit_ids:
            st = sorting.get_unit_spike_train(unit_id)
            spike_counts.append(len(st))
            total_num_spikes += len(st)
            if len(st) > 0:
                max_time = max(max_time, np.max(st) / sorting.get_sampling_frequency())
        total_duration_sec = max_time  # we assume the start time is 0

        output_h5_fname = "output.h5"
        with h5py.File(output_h5_fname, "w") as f:
            f.attrs["type"] = "spike_sorting_summary"
            f.attrs["format_version"] = 1
            f.attrs["unit_ids"] = unit_ids
            f.attrs["sampling_frequency"] = sampling_frequency
            f.attrs["total_duration_sec"] = total_duration_sec
            f.attrs["total_num_spikes"] = total_num_spikes
            _create_spike_trains(
                f=f,
                sorting=sorting,
                total_num_spikes=total_num_spikes,
                total_duration_sec=total_duration_sec,
                unit_ids=unit_ids,
                spike_counts=spike_counts,
            )
            _create_autocrorrelograms(
                f=f,
                sorting=sorting,
                unit_ids=unit_ids,
                window_size_msec=100,
                bin_size_msec=1,
            )
        output_nh5_fname = "output.nh5"
        h5_to_nh5(output_h5_fname, output_nh5_fname)
        context.output.upload(output_nh5_fname)


def _create_spike_trains(
    f: "h5py.File",
    sorting: "si.BaseSorting",
    total_num_spikes: int,
    total_duration_sec: float,
    unit_ids: list,
    spike_counts: list,
):
    sampling_frequency = sorting.get_sampling_frequency()

    avg_num_spikes_per_chunk = 500000
    approx_num_chunks = int(np.ceil(total_num_spikes / avg_num_spikes_per_chunk))

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
    print(f"Using {num_chunks} chunks of duration {duration_per_chunk_sec} sec")
    chunk_start_times = []
    chunk_end_times = []
    for i in range(num_chunks):
        start_time = i * duration_per_chunk_sec
        end_time = min((i + 1) * duration_per_chunk_sec, total_duration_sec)
        chunk_start_times.append(start_time)
        chunk_end_times.append(end_time)
    spike_trains_group = f.create_group("spike_trains")
    spike_trains_group.attrs["type"] = "spike_trains"
    spike_trains_group.attrs["unit_ids"] = unit_ids
    spike_trains_group.attrs["chunk_start_times"] = chunk_start_times
    spike_trains_group.attrs["chunk_end_times"] = chunk_end_times
    spike_trains_group.attrs["sampling_frequency"] = sorting.get_sampling_frequency()
    spike_trains_group.attrs["total_duration_sec"] = total_duration_sec
    spike_trains_group.attrs["total_num_spikes"] = total_num_spikes
    spike_trains_group.attrs["spike_counts"] = spike_counts
    for i in range(len(chunk_start_times)):
        start_time = chunk_start_times[i]
        end_time = chunk_end_times[i]
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
        for jj in range(len(chunk_spike_trains)):
            ind += len(chunk_spike_trains[jj])
            spike_times_index.append(ind)
        spike_times_index = np.array(spike_times_index, dtype=np.int32)
        spike_trains_group.create_dataset(f"chunk_{i}/spike_times", data=spike_times)
        spike_trains_group.create_dataset(
            f"chunk_{i}/spike_times_index", data=spike_times_index
        )


def _create_autocrorrelograms(
    f: "h5py.File",
    sorting: "si.BaseSorting",
    unit_ids: list,
    window_size_msec: int = 100,
    bin_size_msec: int = 1,
):
    from .compute_correlogram_data import compute_correlogram_data

    bin_counts_list = []
    for unit_id in unit_ids:
        a = compute_correlogram_data(
            sorting=sorting,
            unit_id1=unit_id,
            window_size_msec=window_size_msec,
            bin_size_msec=bin_size_msec,
        )
        bin_edges_sec = a["bin_edges_sec"]
        bin_counts = a["bin_counts"]
        bin_counts_list.append(bin_counts)
    num_bins = len(bin_edges_sec) - 1
    all_bin_counts = np.zeros((len(unit_ids), num_bins), dtype=np.int32)
    for i in range(len(unit_ids)):
        all_bin_counts[i, :] = bin_counts_list[i]
    autocorrelograms_group = f.create_group("autocorrelograms")
    autocorrelograms_group.attrs["type"] = "autocorrelograms"
    autocorrelograms_group.attrs["unit_ids"] = unit_ids
    autocorrelograms_group.create_dataset("bin_edges_sec", data=np.array(bin_edges_sec).astype(
        np.float32
    ))
    autocorrelograms_group.create_dataset("bin_counts", data=all_bin_counts)
