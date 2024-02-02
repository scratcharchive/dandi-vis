from typing import Optional
import dendro.client as den


def vis_spike_trains(
    project: den.Project,
    nwb_file_name: str,
    dandiset_id: str,
    units_path: str,
    sampling_frequency: Optional[float],
):
    nwb_file_name_2 = nwb_file_name[len(f"imported/{dandiset_id}/") :]
    output_file_name = (
        f"generated/{dandiset_id}/" + nwb_file_name_2 + "/spike_trains.nh5"
    )
    den.submit_job(
        project=project,
        processor_name="dandi-vis-1.spike_trains",
        input_files=[den.SubmitJobInputFile(name="input", file_name=nwb_file_name)],
        output_files=[
            den.SubmitJobOutputFile(
                name="output",
                file_name=output_file_name,
            )
        ],
        parameters=[
            den.SubmitJobParameter(name="units_path", value=units_path),
            den.SubmitJobParameter(name="sampling_frequency", value=sampling_frequency),
        ],
        required_resources=den.DendroJobRequiredResources(
            numCpus=2, numGpus=0, memoryGb=4, timeSec=60 * 60
        ),
        run_method="local",
    )
    f = project.get_file(output_file_name)
    type0 = "spike_trains"
    label0 = "Spike trains"
    if f is None:
        status0 = "submitted"
        figurl0 = None
    elif (
        f is not None and f._file_data.content == "pending"
    ):  # todo: expose this in the dendro API somehow
        status0 = "pending"
        figurl0 = None
    else:
        url = f.get_url()
        figurl0 = f"https://figurl.org/f?v=https://figurl-dandi-vis.surge.sh&d=%7B%22type%22:%22spike_trains_nh5%22,%22nh5_file%22:%22{url}%22%7D&label={nwb_file_name_2}/spike_trains.nh5"
        status0 = "done"
    return {
        "type": type0,
        "label": label0,
        "status": status0,
        "figurl": figurl0,
    }
