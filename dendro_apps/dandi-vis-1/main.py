#!/usr/bin/env python


from dendro.sdk import App
from tuning_curves_2d.tuning_curves_2d import TuningCurves2DProcessor
from spike_trains.spike_trains import SpikeTrainsProcessor

app = App(
    name="dandi-vis-1",
    description="Miscellaneous processors for dandi-vis",
    app_image="ghcr.io/magland/dandi-vis-1:latest",
    app_executable="/app/main.py",
)


app.add_processor(TuningCurves2DProcessor)
app.add_processor(SpikeTrainsProcessor)

if __name__ == "__main__":
    app.run()
