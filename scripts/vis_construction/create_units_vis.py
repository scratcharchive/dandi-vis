from typing import List, Union
import numpy as np
import h5py
import spikeinterface as si
import sortingview.views as vv
import remfile
from .compute_correlograms_data import compute_correlogram_data

# with remfile support
from .NwbExtractors import NwbSortingExtractor


def create_units_vis(url):
    sorting = NwbSortingExtractor(url, stream_mode="remfile")
    remf = remfile.File(url)
    with h5py.File(remf, 'r') as file:
        v_rp = create_raster_plot(sorting=sorting)
        v_ac = create_autocorrelograms(sorting=sorting)
        v_u = create_units_table(unit_ids=sorting.get_unit_ids(), file=file)

    v_right = vv.Splitter(
        item1=vv.LayoutItem(v_u),
        item2=vv.LayoutItem(v_rp),
        direction='vertical'
    )

    v = vv.Splitter(
        item1=vv.LayoutItem(v_ac, stretch=1),
        item2=vv.LayoutItem(v_right, stretch=2),
        direction='horizontal'
    )

    return v


def create_raster_plot(
    *, sorting: si.BaseSorting, height=500
):
    plot_items: List[vv.RasterPlotItem] = []
    min_spike_time = np.inf
    max_spike_time = -np.inf
    for unit_id in sorting.get_unit_ids():
        spike_times_sec = (
            np.array(sorting.get_unit_spike_train(segment_index=0, unit_id=unit_id))
            / sorting.get_sampling_frequency()
        )
        min_spike_time = min(min_spike_time, np.min(spike_times_sec))
        max_spike_time = max(max_spike_time, np.max(spike_times_sec))
        plot_items.append(
            vv.RasterPlotItem(
                unit_id=unit_id, spike_times_sec=spike_times_sec.astype(np.float32)
            )
        )
    
    # Let's start at 0
    if min_spike_time > 0:
        min_spike_time = 0

    view = vv.RasterPlot(
        start_time_sec=min_spike_time,
        end_time_sec=max_spike_time,
        plots=plot_items,
        height=height,
    )
    return view

def create_autocorrelograms(*, sorting: si.BaseSorting):
    autocorrelogram_items: List[vv.AutocorrelogramItem] = []
    for unit_id in sorting.get_unit_ids():
        a = compute_correlogram_data(sorting=sorting, unit_id1=unit_id, unit_id2=None, window_size_msec=50, bin_size_msec=1)
        bin_edges_sec = a["bin_edges_sec"]
        bin_counts = a["bin_counts"]
        autocorrelogram_items.append(vv.AutocorrelogramItem(unit_id=unit_id, bin_edges_sec=bin_edges_sec, bin_counts=bin_counts))
    view = vv.Autocorrelograms(autocorrelograms=autocorrelogram_items)
    return view

def create_units_table(*, unit_ids: List[Union[int, str]], file: h5py.File):
    colnames = file['/units'].attrs['colnames']
    columns: List[vv.UnitsTableColumn] = []

    values_for_columns = {}
    for c in colnames:
        a = file['/units'][c]
        if a.ndim == 1 and a.shape[0] == len(unit_ids):
            print(f"Found column {c}")
            if a.dtype == np.float32:
                dd = "float"
                values = a[()].tolist()
            elif a.dtype == np.float64:
                dd = "float"
                values = a[()].astype(np.float32).tolist()
            elif a.dtype == np.int32:
                dd = "int"
                values = a[()].tolist()
            elif a.dtype == np.int64:
                dd = "int"
                values = a[()].astype(np.int32).tolist()
            elif a.dtype == np.int16:
                dd = "int"
                values = a[()].astype(np.int32).tolist()
            elif a.dtype == np.dtype('O'):
                dd = "string"
                values = [v.decode('utf-8') for v in a[()]]
            elif a.dtype == np.dtype('S'):
                dd = "string"
                values = [v.decode('utf-8') for v in a[()]]
            else:
                dd = None
                values = None
            columns.append(vv.UnitsTableColumn(key=c, label=c, dtype=dd))
            values_for_columns[c] = values
    
    rows: List[vv.UnitsTableRow] = []
    for unit_id in unit_ids:
        values = {"unitId": unit_id}
        for c in columns:
            values[c.key] = values_for_columns[c.key][unit_id]
        rows.append(vv.UnitsTableRow(unit_id=unit_id, values=values))
    view = vv.UnitsTable(columns=columns, rows=rows)
    return view
