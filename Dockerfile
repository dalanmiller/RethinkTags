FROM ubuntu
MAINTAINER Daniel Alan Miller <dalanmiller@rethinkdb.com>

#Get the main things
RUN apt-get update
RUN apt-get install -y build-essential wget curl 
RUN echo "deb http://download.rethinkdb.com/apt `lsb_release -cs` main" \
| sudo tee /etc/apt/sources.list.d/rethinkdb.list \
&& wget -qO- http://download.rethinkdb.com/apt/pubkey.gpg \
| sudo apt-key add -

RUN apt-get update
RUN apt-get install -y rethinkdb python-pip git supervisor

#Get RethinkTags
RUN git clone https://github.com/dalanmiller/RethinkTags.git
RUN cd RethinkTags
RUN pip install -r RethinkTags/requirements.txt 
RUN cp rethinktags.conf /etc/supervisor/conf.d/

#Run RethinkTags
supervisorctl reread 
supervisorctl update




