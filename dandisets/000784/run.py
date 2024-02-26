import os
from jinja2 import Environment, FileSystemLoader
import dendro.client as den

# Add .. to the path so we can import from the common directory
import sys

sys.path.append(os.path.join(os.path.dirname(__file__), ".."))
from common.vis_spike_sorting_summary import vis_spike_sorting_summary
from common._get_nwb_file_paths import _get_nwb_file_paths


thisdir = os.path.dirname(os.path.abspath(__file__))

num_bins = 30


def main():
    dandiset_id = "000784"
    dandiset_version = "draft"
    project_id = "c031e7bd"
    
    # Load the project
    project = den.load_project(project_id)

    nwb_file_names = _get_nwb_file_paths(project, f"imported/{dandiset_id}")

    files_out = []
    for nwb_file_name in nwb_file_names:
        name = nwb_file_name[len(f"imported/{dandiset_id}/") :]
        x = {"nwb_file_name": name, "visualizations": []}
        print(f"Processing {name}")

        # spike sorting summary
        f = project.get_file(f'generated/{dandiset_id}/{name}/spike_sorting_summary.nh5')
        if f is not None:
            if f._file_data.content.startswith('url:'):
                url = f.get_url()
                figurl0 = f"https://figurl.org/f?v=npm://@fi-sci/figurl-dandi-vis@0.1/dist&d=%7B%22nh5%22:%22{url}%22%7D&label={name}/spike_sorting_summary.nh5"
                status = 'done'
            elif f._file_data.content == 'pending':
                status = 'pending'
                figurl0 = ''
            else:
                status = 'unknown'
                figurl0 = ''
            x['visualizations'].append({
                'type': 'spike_sorting_summary',
                'label': 'Spike sorting summary',
                'status': status,
                'figurl': figurl0
            })
        

        ff = project.get_file(nwb_file_name)
        x["neurosift_url"] = (
            f"https://flatironinstitute.github.io/neurosift/?p=/nwb&url={ff.get_url()}&dandisetId={dandiset_id}&dandisetVersion={dandiset_version}"
        )

        files_out.append(x)

    data = {"dandiset_id": dandiset_id, "files": files_out}

    env = Environment(loader=FileSystemLoader(thisdir + '/../common/templates'))
    template = env.get_template("dandiset.template.md")
    file_out = template.render(**data)
    out_fname = os.path.join(thisdir, f"{dandiset_id}.md")
    with open(out_fname, "w") as f:
        f.write(file_out)

if __name__ == "__main__":
    main()
