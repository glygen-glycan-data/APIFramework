FROM glyomics/apiframework:latest

RUN mkdir -p /code /code/image
RUN python -m pip install requests
COPY Glymage.ini Glymage.py /code/
COPY htmls /code/htmls/
ADD image/image.tgz /code/image/
RUN chmod a+rwx /code/image/hash /code/image/snfg /code/image/snfg/extended /code/image/snfg/compact
WORKDIR /code
CMD python Glymage.py
