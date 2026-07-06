FROM glyomics/apiframework:latest
RUN rm -f /code/pygly/GlycoCT2ImageBundle.jar
ARG CACHEBUSTER=1
ADD . /code
WORKDIR /code
CMD python Substructure.py
