FROM glyomics/apiframework:latest

RUN mkdir -p /code /code/image
RUN python -m pip install requests
COPY Glymage.ini Glymage.py /code/
COPY htmls /code/htmls/
COPY js /code/js/
COPY css /code/css/
COPY demo /code/demo/
ADD image/image.tgz /code/image/
RUN mkdir -p /code/image /code/image/hash /code/image/snfg /code/image/snfg/extended /code/image/snfg/compact /code/image/cfg /code/image/cfg/extended /code/image/cfg/compact
RUN chmod a+rwx /code/image /code/image/hash /code/image/snfg /code/image/snfg/extended /code/image/snfg/compact /code/image/cfg /code/image/cfg/extended /code/image/cfg/compact
WORKDIR /code
CMD python Glymage.py
