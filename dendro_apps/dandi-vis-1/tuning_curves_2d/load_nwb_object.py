import pynwb


def load_nwb_object(nwbfile: pynwb.NWBFile, path: str):
    """
    Load an object from an NWB file given its path.
    """
    path_parts = [p for p in path.split("/") if p]
    obj = nwbfile
    for i, part in enumerate(path_parts):
        if i == 0:
            if part == "processing":
                obj = obj.processing
                continue
            elif part == "units":
                obj = obj.units
                continue
        obj = obj[part]
    return obj
