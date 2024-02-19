FROM python:3.9

# Install pynwb
RUN pip install pynwb==2.5.0

# Install spikeinterface
RUN pip install spikeinterface==0.99.1

# Install pynapple
RUN pip install pynapple==0.5.0

# Install mountainsort5
RUN pip install mountainsort5==0.5.3

# Install nh5
RUN pip install nh5==0.1.3

# Install dendro
RUN pip install dendro==0.2.6

# Install dendroextractors
RUN pip install dendroextractors==0.1.4

# # Install dendro from github
# RUN git clone https://github.com/flatironinstitute/dendro.git /src/dendro \
#     && cd /src/dendro/python \
#     && git checkout file-cache \
#     && pip install -e . && echo "3"

# Copy files into the container
RUN mkdir /app
COPY *.py /app/
COPY tuning_curves_2d/*.py /app/tuning_curves_2d/
COPY spike_sorting_summary/*.py /app/spike_sorting_summary/
COPY ecephys_summary/*.py /app/ecephys_summary/
