import dendro.client as den


def vis_tuning_curves_2d(project: den.Project, nwb_file_name: str, dandiset_id: str, num_bins: int = 30):
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
    type0 = "tuning_curves_2d"
    label0 = "2D tuning curves"
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
        figurl0 = f"https://figurl.org/f?v=npm://@fi-sci/figurl-dandi-vis@0.1/dist&d=%7B%22nh5%22:%22{url}%22%7D&label={nwb_file_name_2}/tuning_curves_2d.nh5"
        status0 = "done"
    return {
        "type": type0,
        "label": label0,
        "status": status0,
        "figurl": figurl0,
    }
