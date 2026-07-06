FROM python:3.12

ARG CACHEBUSTER=1

ADD . /code
WORKDIR /code
RUN pip install -r requirement.txt
RUN ./environment.sh

CMD python test.py
