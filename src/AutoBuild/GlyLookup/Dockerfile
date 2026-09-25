FROM glyomics/apiframework:latest
ARG CACHEBUSTER=1
ARG IMAGE_TAG=unknown
ENV DOCKER_TAG=$IMAGE_TAG
ADD . /code
WORKDIR /code
CMD ["python", "GlyLookup.py"]
