FROM deviantony/python-dev

RUN apt-key adv --keyserver keyserver.ubuntu.com --recv-keys 1C4CBDCDCD2EFD2A
RUN echo 'deb http://repo.percona.com/apt trusty main\ndeb-src http://repo.percona.com/apt trusty main'\
 > /etc/apt/sources.list.d/percona.list

RUN apt-get update && apt-get install -y mysql-server percona-xtrabackup

COPY requirements.txt /tmp/requirements.txt
RUN /bin/zsh -c 'source ~/.zshrc; workon python3; pip install -r /tmp/requirements.txt'
RUN /bin/zsh -c 'source ~/.zshrc; workon python2.7; pip install -r /tmp/requirements.txt'

RUN echo "export PYTHONPATH=${PYTHONPATH}" >> /root/.zshrc

COPY tests/prepare_database.sql /sql/prepare_database.sql
COPY tests/insert_data.sql /sql/insert_data.sql

RUN /etc/init.d/mysql start && cat /sql/prepare_database.sql | mysql -u root
