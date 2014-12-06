FROM deviantony/python

ADD . /tmp
RUN cd /tmp
ENTRYPOINT ["tox"]
