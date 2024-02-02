import os
from jinja2 import Environment, FileSystemLoader
import dendro.client as den

# Add .. to the path so we can import from the common directory
import sys

sys.path.append(os.path.join(os.path.dirname(__file__), ".."))
from common.vis_spike_trains import vis_spike_trains
from common._get_nwb_file_paths import _get_nwb_file_paths


thisdir = os.path.dirname(os.path.abspath(__file__))

num_bins = 30


def main():
    dandiset_id = "000784"
    dandiset_version = "draft"
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

        ff = project.get_file(nwb_file_name)
        file_out["neurosift_url"] = (
            f"https://flatironinstitute.github.io/neurosift/?p=/nwb&url={ff.get_url()}&dandisetId={dandiset_id}&dandisetVersion={dandiset_version}"
        )

        files_out.append(file_out)

    data = {"dandiset_id": dandiset_id, "files": files_out}

    env = Environment(loader=FileSystemLoader(thisdir + '/../common/templates'))
    template = env.get_template("dandiset.template.md")
    file_out = template.render(**data)
    out_fname = os.path.join(thisdir, f"{dandiset_id}.md")
    with open(out_fname, "w") as f:
        f.write(file_out)


if __name__ == "__main__":
    main()
