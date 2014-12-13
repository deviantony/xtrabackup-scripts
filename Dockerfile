FROM deviantony/python-dev

RUN apt-get install -y mysql-server
ADD . /python
