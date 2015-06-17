FROM ubuntu
MAINTAINER Daniel Alan Miller <dalanmiller@rethinkdb.com>

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



