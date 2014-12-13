FROM deviantony/python-dev

RUN apt-get install -y mysql-server

ADD requirements.txt /tmp/requirements.txt
RUN /bin/zsh -c 'source ~/.zshrc; workon python3; pip install -r /tmp/requirements.txt'

RUN echo "export PYTHONPATH=${PYTHONPATH}:/python" >> /root/.zshrc
