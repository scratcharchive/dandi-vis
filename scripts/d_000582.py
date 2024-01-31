from dandi_nwb_meta import load_dandi_nwb_meta_output, DandiNwbMetaAsset
import spikeinterface as si
import spikeinterface.extractors as se

# with remfile support
from NwbExtractors import NwbSortingExtractor


def d_000582():
    dandiset_id = '000582'
    dandi_nwb_meta_dandiset = load_dandi_nwb_meta_output(dandiset_id)
    if dandi_nwb_meta_dandiset is None:
        raise Exception(f"Failed to load nwb meta output for {dandiset_id}")
    for asset in dandi_nwb_meta_dandiset.nwb_assets:
        print(f'Processing {asset.asset_path}')
        _process_asset(asset)
        break  # for now only process the first asset


def _process_asset(asset: DandiNwbMetaAsset):
    # Load the NWB file
    # url = asset.download_url  # in the future the download_url will be available
    url = f'https://api.dandiarchive.org/api/assets/{asset.asset_id}/download/'
    sorting = se.NwbSortingExtractor(url, stream_mode='remfile')
    