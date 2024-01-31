from typing import List
import os
import urllib.error
import json
import gzip
from tempfile import TemporaryDirectory
from pydantic import BaseModel, Field
from h5tojson import H5ToJsonFile


class DandiNwbMetaAsset(BaseModel):
    asset_id: str = Field(description="Asset identifier")
    asset_path: str = Field(description="Asset path")
    nwb_metadata: H5ToJsonFile = Field(description="NWB metadata")


class DandiNwbMetaDandiset(BaseModel):
    dandiset_id: str = Field(description="Dandiset identifier")
    dandiset_version: str = Field(description="Dandiset version")
    nwb_assets: List[DandiNwbMetaAsset] = Field(description="List of assets")


def load_dandi_nwb_meta_output(dandiset_id: str):
    with TemporaryDirectory() as tempdir:
        tmp_output_fname = os.path.join(tempdir, "output.json.gz")
        try:
            object_key = _get_object_key_for_dandi_nwb_meta_output(dandiset_id)
            url = f"https://neurosift.org/{object_key}"
            _download_file(url, tmp_output_fname)
        except urllib.error.HTTPError:
            return None
        return _load_dandi_nwb_meta_output_from_file(tmp_output_fname)


def _load_dandi_nwb_meta_output_from_file(output_fname: str) -> DandiNwbMetaDandiset:
    if os.path.exists(output_fname):
        if output_fname.endswith(".gz"):
            with open(output_fname, "rb") as f:
                existing = json.loads(gzip.decompress(f.read()))
                existing = DandiNwbMetaDandiset(**existing)
        else:
            with open(output_fname, "r") as f:
                existing = json.load(f)
                existing = DandiNwbMetaDandiset(**existing)
    else:
        existing = None
    return existing


def _download_file(url: str, output_fname: str):
    """Downloads a file from a URL."""
    with open(output_fname, "wb") as f:
        # The User-Agent header is required so that cloudflare doesn't block the request
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req) as response:
            chunk_size = 1024
            while True:
                chunk = response.read(chunk_size)
                if not chunk:
                    break
                f.write(chunk)


def _get_object_key_for_dandi_nwb_meta_output(dandiset_id: str) -> str:
    return f"dandi-nwb-meta/dandisets/{dandiset_id}.json.gz"
