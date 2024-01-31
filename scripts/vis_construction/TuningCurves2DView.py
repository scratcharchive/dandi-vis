from typing import List, Union
import numpy as np
import figurl
import kachery_cloud as kcl


class TuningCurves2DView:
    def __init__(
        self,
        *,
        rate_maps: List[np.ndarray],
        x_bin_positions: np.ndarray,
        y_bin_positions: np.ndarray,
        unit_ids: List[Union[str, int]],
        unit_num_spikes: List[int],
    ):
        self.rate_maps = rate_maps
        self.x_bin_positions = x_bin_positions
        self.y_bin_positions = y_bin_positions
        self.unit_ids = unit_ids
        self.unit_num_spikes = unit_num_spikes

    def url(self, *, label: str):
        view_data = figurl.serialize_data(
            {
                "type": "tuning_curves_2d",
                "tuning_curves_2d": [
                    {
                        "unit_id": self.unit_ids[i],
                        "values": self.rate_maps[i].astype(np.float32),
                        "num_spikes": self.unit_num_spikes[i],
                    }
                    for i in range(len(self.unit_ids))
                ],
                "x_bin_positions": self.x_bin_positions.astype(np.float32),
                "y_bin_positions": self.y_bin_positions.astype(np.float32),
            }
        )
        data_uri = kcl.store_json(view_data)
        v = 'https://figurl-tuning-curves-1.surge.sh'
        label_enc = label.replace(' ', '%20')
        view_url = f"https://figurl.org/f?v={v}&d={data_uri}&label={label_enc}"
        return view_url