FROM glyomics/apiframework:latest

RUN rm -f /code/pygly/GlycoCT2ImageBundle.jar
ADD . /code

WORKDIR /code

CMD python Substructure.py
