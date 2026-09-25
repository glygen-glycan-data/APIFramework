FROM glyomics/apiframework:latest
RUN rm -f /code/pygly/GlycoCT2ImageBundle.jar
ARG CACHEBUSTER=1
ARG IMAGE_TAG=unknown
ENV DOCKER_TAG=$IMAGE_TAG
ADD . /code
WORKDIR /code
CMD python Substructure.py
