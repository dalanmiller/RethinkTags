FROM ubuntu
MAINTAINER Daniel Alan Miller <dalanmiller@rethinkdb.com>

#Edit the sources.list
RUN ["echo", "-e", "deb mirror://mirrors.ubuntu.com/mirrors.txt trusty main restricted universe multiverse\
deb mirror://mirrors.ubuntu.com/mirrors.txt trusty-updates main restricted universe multiverse\
deb mirror://mirrors.ubuntu.com/mirrors.txt trusty-backports main restricted universe multiverse\
deb mirror://mirrors.ubuntu.com/mirrors.txt trusty-security main restricted universe multiverse\
", "|", "cat", "-", "/etc/apt/sources.list", ">", "/tmp/out", "&&", "mv", "/tmp/out", "/etc/apt/sources.list"]

RUN head /etc/apt/sources.list

#Get the main things
RUN apt-get update
RUN apt-get install -y git curl build-essential python-dev && \
rm -rf /var/lib/apt/lists/* && \
apt-get clean

RUN curl https://bootstrap.pypa.io/get-pip.py | python
RUN pip install -U pip

#Get RethinkTags
RUN mkdir -p /home/app

ADD . /home/app
RUN pip install -Ur /home/app/requirements.txt

#Run RethinkTags
WORKDIR /home/app
CMD ["python",  "/home/app/app.py"]

EXPOSE 8000



