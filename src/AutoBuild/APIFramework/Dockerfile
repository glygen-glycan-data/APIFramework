FROM python:2.7

ADD . /code

WORKDIR /code

ENV WEBSERVICE_BASIC_HOST=0.0.0.0

RUN pip install -r requirement.txt

CMD python test.py
