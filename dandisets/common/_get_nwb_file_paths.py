from typing import List
import dendro.client as den


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
