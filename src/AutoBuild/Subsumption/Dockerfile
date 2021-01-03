FROM glyomics/apiframework:0.0.1

ADD . /code

WORKDIR /code

RUN apt-get update && \
    apt-get install -y openjdk-11-jre-headless && \
    apt-get clean;

CMD python Subsumption.py


