from typing import List, Optional
import os
from jinja2 import Environment, FileSystemLoader
import dendro.client as den


thisdir = os.path.dirname(os.path.abspath(__file__))

num_bins = 30


def main():
    dandiset_id = "000784"
    project_id = "c031e7bd"
    units_path = "/processing/ecephys/units"
    sampling_frequency = 30000  # need to hardcode for now b/c sorting extractor not finding the recording.

    # Load the project
    project = den.load_project(project_id)

    nwb_file_names = _get_nwb_file_paths(project, f"imported/{dandiset_id}")

    files_out = []
    for nwb_file_name in nwb_file_names:
        nwb_file_name_2 = nwb_file_name[len(f"imported/{dandiset_id}/") :]
        file_out = {"nwb_file_name": nwb_file_name_2, "visualizations": []}
        print(f"Processing {nwb_file_name_2}")

        v = vis_spike_trains(
            project=project,
            nwb_file_name=nwb_file_name,
            dandiset_id=dandiset_id,
            units_path=units_path,
            sampling_frequency=sampling_frequency,
        )
        file_out["visualizations"].append(v)

        files_out.append(file_out)

    data = {"dandiset_id": dandiset_id, "files": files_out}

    env = Environment(loader=FileSystemLoader(thisdir))
    template = env.get_template(f"{dandiset_id}.template.md")
    file_out = template.render(**data)
    out_fname = os.path.join(thisdir, f"{dandiset_id}.md")
    if not os.path.exists(os.path.dirname(out_fname)):
        os.makedirs(os.path.dirname(out_fname))
    with open(out_fname, "w") as f:
        f.write(file_out)


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


def _get_nwb_file_paths(project: den.Project, folder_path: str):
    ret: List[str] = []
    folder = project.get_folder(folder_path)
    files = folder.get_files()
    for file in files:
        ret.append(file.file_name)
    folders = folder.get_folders()
    for f in folders:
        a = _get_nwb_file_paths(project, f.path)
        ret.extend(a)
    return ret


if __name__ == "__main__":
    main()
