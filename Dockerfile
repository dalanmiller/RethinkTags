FROM rethinkdb
MAINTAINER Daniel Alan Miller <dalanmiller@rethinkdb.com>

#Get the main things
RUN apt-get update
RUN apt-get install -y git python-pip supervisor build-essential python-dev

#Get RethinkTags
RUN mkdir -p /home/app
#RUN git clone https://github.com/dalanmiller/RethinkTags.git /home/app
ADD . /home/app
RUN ls /home/app
RUN pip install -Ur /home/app/requirements.txt

#Move secret.py into app folder
ADD ./secret.py /home/app/secret.py

RUN ls /home/app

#Run RethinkTags
WORKDIR /home/app
CMD ["python",  "/home/app/app.py"]
