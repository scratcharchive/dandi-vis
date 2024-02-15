FROM python:3.9

# Install neuroconv
RUN pip install neuroconv

# Install spikeinterface
RUN pip install spikeinterface==0.100.0

# Install dendro
RUN pip install dendro==0.2.3

# Copy files into the container
RUN mkdir /app
COPY *.py /app/
COPY create_subrecording/*.py /app/create_subrecording/
