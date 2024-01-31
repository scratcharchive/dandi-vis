from typing import List
import json
from pydantic import BaseModel
import urllib.request


class Dandiset(BaseModel):
    dandiset_id: str
    version: str


def fetch_all_dandisets():
    url = "https://api.dandiarchive.org/api/dandisets/?page=1&page_size=5000&ordering=-modified&draft=true&empty=false&embargoed=false"
    with urllib.request.urlopen(url) as response:
        X = json.loads(response.read())

    dandisets: List[Dandiset] = []
    for ds in X["results"]:
        pv = ds["most_recent_published_version"]
        dv = ds["draft_version"]
        dandisets.append(
            Dandiset(
                dandiset_id=ds["identifier"],
                version=pv["version"] if pv else dv["version"],
            )
        )

    return dandisets
