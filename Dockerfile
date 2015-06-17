FROM ubuntu
MAINTAINER Daniel Alan Miller <dalanmiller@rethinkdb.com>

#Get the main things
RUN apt-get update
RUN apt-get install -y git python-pip build-essential python-dev && \
rm -rf /var/lib/apt/lists/*

#Get RethinkTags
RUN mkdir -p /home/app

ADD . /home/app
RUN pip install -Ur /home/app/requirements.txt

#Run RethinkTags
WORKDIR /home/app
CMD ["python",  "/home/app/app.py"]

EXPOSE 8000



