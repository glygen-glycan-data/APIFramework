FROM glyomics/apiframework:latest

ADD . /code

WORKDIR /code

RUN apt-get update && \
    apt-get install -y openjdk-11-jre-headless && \
    apt-get clean;

CMD python Subsumption.py


