FROM glyomics/apiframework:latest

RUN apt-get update && apt-get install -y libgl1

# This ensures cache busting whenever you create a new docker build
ARG CACHEBUST=1
ENV CACHEBUST=${CACHEBUST}

ADD . /code

RUN pip install -r /code/requirements.txt

# Install additional requirements for WebApplication
RUN pip install -r /code/WebApplication/requirements.txt

WORKDIR /code

# Create write permission for WebApplication subdirectory
RUN chmod +x /code/permission.sh
RUN ./permission.sh

# Set working directory to /code/WebApplication
WORKDIR /code/WebApplication

# run the python file
CMD python GlyImageExtractor.py

