from typing import List
import os
from jinja2 import Environment, FileSystemLoader
import dendro.client as den


thisdir = os.path.dirname(os.path.abspath(__file__))

num_bins = 30


def main():
    dandiset_id = "000582"
    project_id = "a7852166"

    # Load the project
    project = den.load_project(project_id)

    nwb_file_names = _get_nwb_file_paths(project, f"imported/{dandiset_id}")

    files_out = []
    for nwb_file_name in nwb_file_names:
        nwb_file_name_2 = nwb_file_name[len(f"imported/{dandiset_id}/") :]
        file_out = {"nwb_file_name": nwb_file_name_2, "visualizations": []}
        print(f"Processing {nwb_file_name_2}")

        v = vis_tuning_curves_2d(
            project=project, nwb_file_name=nwb_file_name, dandiset_id=dandiset_id
        )
        file_out["visualizations"].append(v)

        # v = vis_units_vis(
        #     project=project, nwb_file_name=nwb_file_name, dandiset_id=dandiset_id
        # )
        # file_out["visualizations"].append(v)

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


def vis_tuning_curves_2d(project: den.Project, nwb_file_name: str, dandiset_id: str):
    nwb_file_name_2 = nwb_file_name[len(f"imported/{dandiset_id}/") :]
    output_file_name = (
        f"generated/{dandiset_id}/" + nwb_file_name_2 + "/tuning_curves_2d.nh5"
    )
    den.submit_job(
        project=project,
        processor_name="dandi-vis-1.tuning_curves_2d",
        input_files=[den.SubmitJobInputFile(name="input", file_name=nwb_file_name)],
        output_files=[
            den.SubmitJobOutputFile(
                name="output",
                file_name=output_file_name,
            )
        ],
        parameters=[
            den.SubmitJobParameter(name="num_bins", value=num_bins),
            den.SubmitJobParameter(
                name="spatial_series_path",
                value="processing/behavior/Position/SpatialSeriesLED1",
            ),
        ],
        required_resources=den.DendroJobRequiredResources(
            numCpus=2, numGpus=0, memoryGb=4, timeSec=60 * 60
        ),
        run_method="local",
    )
    f = project.get_file(output_file_name)
    if f is None:
        return {"type": "2d_tuning_curves", "status": "submitted"}
    elif (
        f is not None and f._file_data.content == "pending"
    ):  # todo: expose this in the dendro API somehow
        return {"type": "2d_tuning_curves", "status": "pending"}
    else:
        url = f.get_url()
        figurl = f"https://figurl.org/f?v=https://figurl-tuning-curves-1.surge.sh&d=%7B%22type%22:%22tuning_curves_2d_nh5%22,%22nh5_file%22:%22{url}%22%7D&label={nwb_file_name_2}/tuning_curves_2d.nh5"
        return {
            "type": "2d_tuning_curves",
            "status": "done",
            "figurl": figurl,
        }


# def vis_units_vis(project: den.Project, nwb_file_name: str, dandiset_id: str):
#     nwb_file_name_2 = nwb_file_name[len(f"imported/{dandiset_id}/") :]
#     output_file_name = (
#         f"generated/{dandiset_id}/" + nwb_file_name_2 + "/units_vis.figurl"
#     )
#     den.submit_job(
#         project=project,
#         processor_name="dendro1.units_vis",
#         input_files=[den.SubmitJobInputFile(name="input", file_name=nwb_file_name)],
#         output_files=[
#             den.SubmitJobOutputFile(
#                 name="output",
#                 file_name=output_file_name,
#             )
#         ],
#         parameters=[],
#         required_resources=den.DendroJobRequiredResources(
#             numCpus=2, numGpus=0, memoryGb=4, timeSec=60 * 60
#         ),
#         run_method="local",
#     )
#     f = project.get_file(output_file_name)
#     if f is None:
#         return {"type": "units", "status": "submitted"}
#     elif (
#         f is not None and f._file_data.content == "pending"
#     ):  # todo: expose this in the dendro API somehow
#         return {"type": "units", "status": "pending"}
#     else:
#         url = f.get_url()
#         print(f'Downloading {url}')
#         figurl = _download_text(url)
#         return {
#             "type": "units",
#             "status": "done",
#             "figurl": figurl,
#         }


def _download_text(url: str):
    from urllib import request

    req = request.Request(
        url,
        headers={"User-Agent": "Mozilla/5.0"},
    )
    with request.urlopen(req) as response:
        return response.read().decode("utf-8")


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
