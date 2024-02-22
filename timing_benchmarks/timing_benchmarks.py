import os
import numpy as np
import time
import h5py
import tempfile
from uuid import uuid4
import requests
import spikeinterface.extractors as se
import spikeinterface.preprocessing as spre
import spikeinterface as si
import remfile
from neuroconv.tools.spikeinterface import (
    write_recording as neuroconv_write_recording
)
import pynwb


# imported/000784/sub-F/sub-F_ses-20230917_obj-34uga6_ecephys.nwb
# neurosift: https://flatironinstitute.github.io/neurosift/?p=/nwb&url=https://api.dandiarchive.org/api/assets/a04169c9-3f75-4dfa-b870-992cfccbde9a/download/&dandisetId=000784&dandisetVersion=draft&dandiAssetPath=sub-F%2Fsub-F_ses-20230917_obj-34uga6_ecephys.nwb
nwb_url = "https://api.dandiarchive.org/api/assets/a04169c9-3f75-4dfa-b870-992cfccbde9a/download/"
electrical_series_path = "/acquisition/ElectricalSeriesAP"
duration_sec = 120
n_jobs = 4
chunk_duration = "2s"


def main():
    with tempfile.TemporaryDirectory() as tmpdir:
        remf = remfile.File(nwb_url)
        h5f = h5py.File(remf, "r")
        data = h5f[electrical_series_path + "/data"]
        assert isinstance(data, h5py.Dataset)
        print(f"Chunking shape: {data.chunks}")

        with TimedTask("Load recording extractor"):
            recording_full = se.NwbRecordingExtractor(
                nwb_url,
                electrical_series_path=electrical_series_path,
                stream_mode="remfile",
            )
            sampling_frequency = recording_full.get_sampling_frequency()
            recording = recording_full.frame_slice(
                start_frame=0, end_frame=int(sampling_frequency * duration_sec)
            )

        with TimedTask("Downloading traces"):
            traces: np.ndarray = recording.get_traces()  # noqa: F841

        with TimedTask("Download equivalent amount of data directly"):
            num_bytes = traces.nbytes
            print(f"Downloading {num_bytes / 1e6:.2f} MB")
            output_file = tmpdir + "/sample.dat"
            buf = _download_file_byte_range(nwb_url, output_file, 0, num_bytes - 1)  # noqa: F841

        with TimedTask("Create recording extractor in memory"):
            recording_memory = se.NumpyRecording(
                [traces], sampling_frequency=sampling_frequency
            )

        with TimedTask("Writing binary recording to disk"):
            si.BinaryRecordingExtractor.write_recording(
                recording=recording_memory,
                file_paths=[tmpdir + "/recording.dat"],
                dtype=recording_memory.dtype,
                n_jobs=n_jobs,
                chunk_duration=chunk_duration,
                mp_context="spawn",
            )
        os.remove(tmpdir + "/recording.dat")

        with TimedTask("Bandpass filtering and writing to disk"):
            recording_filtered = spre.bandpass_filter(
                recording_memory, freq_min=300, freq_max=6000
            )
            si.BinaryRecordingExtractor.write_recording(
                recording=recording_filtered,
                file_paths=[tmpdir + "/recording_filtered.dat"],
                dtype=recording_filtered.dtype,
                n_jobs=n_jobs,
                chunk_duration=chunk_duration,
                mp_context="spawn",
            )
        os.remove(tmpdir + "/recording_filtered.dat")

        with TimedTask("Writing to NWB using neuroconv with compression"):
            nwbfile = _create_dummy_nwbfile()
            neuroconv_write_recording(
                recording_memory,
                nwbfile_path=tmpdir + "/output.nwb",
                nwbfile=nwbfile,
                compression="gzip",
                iterator_type="v2",
                iterator_opts={"display_progress": False},
            )
            file_size = os.path.getsize(tmpdir + "/output.nwb")
            print(f"File size: {file_size / 1e6:.2f} MB")

        with TimedTask("Writing to NWB using neuroconv without compression"):
            nwbfile = _create_dummy_nwbfile()
            neuroconv_write_recording(
                recording_memory,
                nwbfile_path=tmpdir + "/output_no_compression.nwb",
                nwbfile=nwbfile,
                compression=None,
                iterator_type="v2",
                iterator_opts={"display_progress": False},
            )
            file_size = os.path.getsize(tmpdir + "/output_no_compression.nwb")
            print(f"File size: {file_size / 1e6:.2f} MB")

        with TimedTask("Loading recording from local NWB file with compression and writing to disk"):
            recording_local = se.NwbRecordingExtractor(tmpdir + "/output.nwb")
            se.BinaryRecordingExtractor.write_recording(
                recording_local,
                file_paths=[tmpdir + "/recording_local.dat"],
                dtype=recording_local.dtype,
                n_jobs=n_jobs,
                chunk_duration=chunk_duration,
                mp_context="spawn",
            )
        os.remove(tmpdir + "/recording_local.dat")

        with TimedTask("Loading recording from local NWB file without compression and writing to disk"):
            recording_local = se.NwbRecordingExtractor(
                tmpdir + "/output_no_compression.nwb"
            )
            se.BinaryRecordingExtractor.write_recording(
                recording_local,
                file_paths=[tmpdir + "/recording_local_2.dat"],
                dtype=recording_local.dtype,
                n_jobs=n_jobs,
                chunk_duration=chunk_duration,
                mp_context="spawn",
            )
        os.remove(tmpdir + "/recording_local_2.dat")

    for task_name, duration in _timings:
        print(f"{task_name}: {duration:.2f} seconds")


_timings = []


class TimedTask:
    def __init__(self, task_name):
        self.task_name = task_name

    def __enter__(self):
        self.start_time = time.time()
        print(f"Starting [{self.task_name}]...")

    def __exit__(self, *args):
        self.end_time = time.time()
        print(
            f"Finished [{self.task_name}] in {self.end_time - self.start_time:.2f} seconds"
        )
        _timings.append((self.task_name, self.end_time - self.start_time))


def _download_file_byte_range(url: str, dest_file_path: str, start_byte: int, end_byte: int):
    # stream the download
    headers = {'Range': f'bytes={start_byte}-{end_byte}'}
    r = requests.get(url, headers=headers, stream=True, timeout=60 * 60 * 24 * 7)
    if r.status_code != 206:
        raise Exception(f"Failed to download file: {r.status_code} {r.reason}")
    with open(dest_file_path, 'wb') as f:
        for chunk in r.iter_content(chunk_size=1024):
            if chunk:
                f.write(chunk)


def _create_dummy_nwbfile():
    import datetime
    return pynwb.NWBFile(
        session_description='dummy-description',
        identifier=str(uuid4()),
        session_start_time=datetime.datetime(2019, 1, 1),
        experimenter='dummy-experimenter',
        experiment_description='dummy-experiment-description',
        lab='dummy-lab',
        institution='dummy-institution',
        subject=pynwb.file.Subject(
            subject_id='dummy-subject-id',
            age='10',
            date_of_birth=datetime.datetime(2010, 1, 1),
            sex='M',
            species='dummy-species',
            description='dummy-description'
        ),
        session_id='dummy-session-id',
        keywords=['dummy-keyword']
    )


if __name__ == "__main__":
    main()
