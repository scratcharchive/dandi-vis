#!/usr/bin/env python

from dendro.sdk import ProcessorBase, InputFile, OutputFile
from dendro.sdk import BaseModel, Field


class CreateSubrecordingContext(BaseModel):
    input: InputFile = Field(description="Input recording .nwb file")
    output: OutputFile = Field(description="Output recording .nwb file")
    electrical_series_path: str = Field(description="Path to the electrical series in the NWB file")
    start_time_sec: float = Field(description="Start time in seconds")
    end_time_sec: float = Field(description="End time in seconds")


class CreateSubrecordingProcessor(ProcessorBase):
    name = "neuroconv-1.create_subrecording"
    description = "Create a time slice of an ecephys recording in an NWB file"
    label = "neuroconv-1.create_subrecording"
    tags = ["nwb", "ecephys"]
    attributes = {"wip": True}

    @staticmethod
    def run(context: CreateSubrecordingContext):
        import pynwb
        import h5py
        import spikeinterface.extractors as se
        from neuroconv.tools.spikeinterface import write_recording

        file = context.input.get_file()

        print('Loading recording from NWB file')
        recording = se.NwbRecordingExtractor(file=file, electrical_series_path=context.electrical_series_path)  # type: ignore

        print('Getting subrecording')
        start_frame = int(context.start_time_sec * recording.get_sampling_frequency())
        end_frame = int(context.end_time_sec * recording.get_sampling_frequency())
        if end_frame > recording.get_num_frames():
            end_frame = recording.get_num_frames()
        subrecording = recording.frame_slice(
            start_frame=start_frame,
            end_frame=end_frame
        )

        print('Creating new NWB file')
        h5_file = h5py.File(file, 'r')
        with pynwb.NWBHDF5IO(file=h5_file, mode='r') as io:
            nwbfile = io.read()
            new_nwbfile = create_nwbfile(nwbfile)

            print('Writing subrecording to NWB file')
            write_recording(subrecording, nwbfile_path="output.nwb", nwbfile=new_nwbfile)

        print('Uploading the new NWB file')
        context.output.upload('output.nwb')


def create_nwbfile(nwbfile_other):
    import pynwb
    from uuid import uuid4
    return pynwb.NWBFile(
        session_description=nwbfile_other.session_description,
        identifier=str(uuid4()),
        session_start_time=nwbfile_other.session_start_time,
        experimenter=nwbfile_other.experimenter,
        experiment_description=nwbfile_other.experiment_description,
        lab=nwbfile_other.lab,
        institution=nwbfile_other.institution,
        subject=pynwb.file.Subject(
            subject_id=nwbfile_other.subject.subject_id,
            age=nwbfile_other.subject.age,
            date_of_birth=nwbfile_other.subject.date_of_birth,
            sex=nwbfile_other.subject.sex,
            species=nwbfile_other.subject.species,
            description=nwbfile_other.subject.description
        ),
        session_id=nwbfile_other.session_id,
        keywords=nwbfile_other.keywords
    )
