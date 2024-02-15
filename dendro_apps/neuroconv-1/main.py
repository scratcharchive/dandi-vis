#!/usr/bin/env python


from dendro.sdk import App
from create_subrecording.create_subrecording import CreateSubrecordingProcessor 

app = App(
    name="neuroconv-1",
    description="Miscellaneous processors for neuroconv-1",
    app_image="ghcr.io/magland/neuroconv-1:latest",
    app_executable="/app/main.py",
)


app.add_processor(CreateSubrecordingProcessor)

if __name__ == "__main__":
    app.run()
