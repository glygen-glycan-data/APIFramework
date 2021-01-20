FROM python:2.7

ADD . /code

WORKDIR /code

ENV WEBSERVICE_BASIC_HOST=0.0.0.0

RUN pip install -r requirement.txt

RUN chmod 0777 ./
RUN python fixenv.py

CMD python test.py
