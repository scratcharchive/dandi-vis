import json
import os
from dandi_nwb_meta.dandi_nwb_meta import load_dandi_nwb_meta_output
from vis_construction.create_units_vis import create_units_vis
from jinja2 import Environment, FileSystemLoader


thisdir = os.path.dirname(os.path.abspath(__file__))

num_assets_to_process = 5


def d_000582():
    dandiset_id = "000582"
    json_fname = os.path.join(thisdir, f"d_{dandiset_id}.json")
    if not os.path.exists(json_fname):
        dandi_nwb_meta_dandiset = load_dandi_nwb_meta_output(dandiset_id)
        if dandi_nwb_meta_dandiset is None:
            raise Exception(f"Failed to load nwb meta output for {dandiset_id}")
        out_assets = []
        for i, asset in enumerate(dandi_nwb_meta_dandiset.nwb_assets):
            out_assets.append(
                {
                    "path": asset.asset_path,
                    # 'url': asset.download_url  # in the future the download_url will be available
                    "url": f"https://api.dandiarchive.org/api/assets/{asset.asset_id}/download/",
                    "visualizations": [],
                }
            )
            if i + 1 >= num_assets_to_process:
                break
        for out_asset in out_assets:
            print(f"Processing {out_asset['path']}")
            url = out_asset["url"]
            v = create_units_vis(url)
            out_asset["visualizations"].append(
                {
                    "type": "units",
                    "figurl": v.url(label="Units for " + out_asset["path"]),
                }
            )

        with open(json_fname, "w") as f:
            json.dump({"dandiset_id": dandiset_id, "assets": out_assets}, f, indent=4)

    with open(json_fname, "r") as f:
        data = json.load(f)

    env = Environment(loader=FileSystemLoader(thisdir))
    template = env.get_template("d_000582.template.md")
    output = template.render(**data)
    out_fname = os.path.join(thisdir, f"../generated/d_{dandiset_id}.md")
    if not os.path.exists(os.path.dirname(out_fname)):
        os.makedirs(os.path.dirname(out_fname))
    with open(out_fname, "w") as f:
        f.write(output)
