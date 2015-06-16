FROM ubuntu
MAINTAINER Daniel Alan Miller <dalanmiller@rethinkdb.com>


#Get the main things
RUN source /etc/lsb-release \
    && echo "deb http://download.rethinkdb.com/apt $DISTRIB_CODENAME main" \
    | sudo tee /etc/apt/sources.list.d/rethinkdb.list \
    wget -qO- http://download.rethinkdb.com/apt/pubkey.gpg | sudo apt-key add -
RUN apt-get update
RUN apt-get install -y rethinkdb python-pip git supervisor

#Get RethinkTags
RUN git clone https://github.com/dalanmiller/RethinkTags.git
RUN cd RethinkTags
RUN pip install -r requirements.txt 
RUN cp rethinktags.conf /etc/supervisor/conf.d/

#Run RethinkTags
supervisorctl reread 
supervisorctl update




