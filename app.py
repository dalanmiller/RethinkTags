#!/usr/bin/env python
from jinja2 import Environment, FileSystemLoader
from pprint import pprint
import os
from secret import CLIENT_ID, CLIENT_SECRET, ACCESS_TOKEN
from tornado.concurrent import Future
import instagram
import json
import os
import time
import rethinkdb as r
import sys
import tornado.escape
import tornado.gen
import tornado.httpserver
import tornado.ioloop
import tornado.web
import tornado.websocket
import tornado.wsgi
import urllib

template_env = Environment(loader=FileSystemLoader("templates"))

INSTAGRAM_API_URL = "https://api.instagram.com/v1/"
RETHINKDB_HOST = os.environ['RETHINKDB_PORT_28015_TCP_ADDR'] \
    if 'RETHINKDB_PORT_28015_TCP_ADDR' in os.environ else "localhost"
RETHINKDB_PORT = os.environ['RETHINKDB_PORT_28015_TCP_PORT'] \
    if 'RETHINKDB_PORT_28015_TCP_PORT' in os.environ else 28015
RETHINKDB_DB = "think_filter"
REDIRECT_URI = "http://rethinktags.dalanmiller.com/auth"
CALLBACK_URI = "http://rethinktags.dalanmiller.com/echo"

time.sleep(3)

#Setup the database and table
conn = r.connect(RETHINKDB_HOST, RETHINKDB_PORT)

try:
    dbs = r.db_list().run(conn)
    if 'think_filter' not in dbs:
        r.db_create("think_filter").run(conn)

except r.errors.RqlRuntimeError as e:
    sys.stderr.write("Failed to create db\n")
    sys.stderr.write(str(e))
    sys.exit(1)

try:
    tables = r.db("think_filter").table_list().run(conn)
    if "posts" not in tables:
        r.db("think_filter")\
            .table_create("posts")\
            .run(conn)

except r.errors.RqlRuntimeError as e:
    sys.stderr.write("Failed to create table 'posts'\n")
    sys.stderr.write(str(e))
    sys.exit(1)

try:
    
    indexes = r.db("think_filter").table("posts").index_list().run(conn)
    if "created_time" not in indexes:
        r.db("think_filter").table("posts").index_create("created_time").run(conn)

except r.errors.RqlRuntimeError as e:
    sys.stderr.write("Failed to create the fooking index")
    sys.stderr.write(str(e))
    sys.exit(1)


conn.close()

#Change loop type to tornado
r.set_loop_type("tornado")


INSTA_CONFIG = {

    "client_id": CLIENT_ID,
    "client_secret": CLIENT_SECRET,
    "redirect_uri": REDIRECT_URI
}


insta_api = instagram.client.InstagramAPI(**INSTA_CONFIG)

class HomeHandler(tornado.web.RequestHandler):

    @tornado.gen.coroutine
    def prepare(self):
        self.rethinkdb_conn = r.connect(
            RETHINKDB_HOST,
            RETHINKDB_PORT,
            RETHINKDB_DB)

    @tornado.gen.coroutine
    def get(self):

        conn = yield self.rethinkdb_conn

        posts = yield r.table("posts")\
            .order_by(index=r.desc("created_time"))\
            .pluck(
                {"images":{"low_resolution":{"url":True}}},
                {"user":{"username":True}},
                "created_time",
                "link",
                {"caption":{"text":True}})\
            .limit(9)\
            .run(conn)

        output_posts = []
        while(yield posts.fetch_next()):

            if len(output_posts) >= 9:
                break;

            p = yield posts.next()
            output_posts.append(p)

        home_template = template_env.get_template("home.html")

        subscriptions_raw = insta_api.list_subscriptions()
        subscriptions = [x['object_id'] for x in subscriptions_raw['data']]

        self.write(home_template.render(
            auth_url = insta_api.get_authorize_url(),
            posts = output_posts,
            subscriptions = subscriptions
            ))


class GramHandler(tornado.web.RequestHandler):
    """
    Route which will handle the incoming post requests sent to this URL and put the Instagram post into RethinkDB
    """

    @tornado.gen.coroutine
    def get(self):

        self.write(self.get_argument("hub.challenge"))
    
    @tornado.gen.coroutine
    def post(self):

        update_json = tornado.escape.json_decode(self.request.body)

        client = tornado.httpclient.AsyncHTTPClient()

        for update in update_json:

            req = tornado.httpclient.HTTPRequest(
                url= INSTAGRAM_API_URL + "tags/" + update['object_id'] + "/media/recent?access_token=" + ACCESS_TOKEN
            )

            response = yield client.fetch(req)

            grams = tornado.escape.json_decode(response.body)['data']

            connection = r.connect(RETHINKDB_HOST, RETHINKDB_PORT, RETHINKDB_DB)

            conn = yield connection

            yield r.table("posts").insert(grams, conflict="error").run(conn)



class FilterPageHandler(tornado.web.RequestHandler):
    """
    TO DO
    """

    @tornado.gen.coroutine
    def post(self, path):

        new_tag = self.request.arguments['filter'][0]

        #Break basically if we already have a subscription for that tag
        # or if we already have ~25 subscriptions remove the last one
        # and add a new one.
        subs = insta_api.list_subscriptions()

        if len(subs['data']) >= 25:
            insta_api.delete_subscriptions(subs[0]['subscription_id'])

        for sub in subs['data']:
            if new_tag == sub["object_id"]:
                self.finish()

        query_params = dict(
            client_id=CLIENT_ID,
            client_secret=CLIENT_SECRET,
            verify_token=str(hash(new_tag))
            )

        body = urllib.urlencode(dict(
            aspect="media",
            object="tag",
            object_id=new_tag,
            callback_url=CALLBACK_URI
            ))

        url="https://api.instagram.com/v1/subscriptions?%s" % urllib.urlencode(query_params)

        client = tornado.httpclient.AsyncHTTPClient()

        req = tornado.httpclient.HTTPRequest(
            url=url,
            method="POST",
            body=body
            )

        response = yield client.fetch(req)

    @tornado.gen.coroutine
    def delete(self, path):

        tag = path.split("/")[-1]

        subscriptions_raw = insta_api.list_subscriptions()

        sub_id = None
        for sub in subscriptions_raw['data']:
            if sub['object_id'] == tag:
                sub_id = sub['id']

        #If id hasn't been assigned the subscription is not in the list
        if sub_id == None:
            self.finish()

        client = tornado.httpclient.AsyncHTTPClient()

        query_params = dict(
            client_secret=CLIENT_SECRET,
            client_id=CLIENT_ID,
            id=sub_id
        )

        url = "https://api.instagram.com/v1/subscriptions?{}".format(urllib.urlencode(query_params))

        req = tornado.httpclient.HTTPRequest(
            url=url,
            method="DELETE"
        )

        response = yield client.fetch(req)

    @tornado.gen.coroutine
    def head(self, path):

        client = tornado.httpclient.AsyncHTTPClient()

        query_params = dict(
            client_id = CLIENT_ID,
            client_secret = CLIENT_SECRET,
            object = "all"
            )

        req = tornado.httpclient.HTTPRequest(
            url="https://api.instagram.com/v1/subscriptions?%s" % urllib.urlencode(query_params),
            method = "DELETE"
        )

        client.fetch(req)

listeners = set()

@tornado.gen.coroutine
def emit_gram():
    while True:
        try:
            conn = yield r.connect(
       		 RETHINKDB_HOST,
        	 RETHINKDB_PORT,
        	 RETHINKDB_DB)

            feed = yield r.table("posts")\
        	.pluck(
            {"images":{"low_resolution":{"url":True}}},
            {"user":{"username":True}},
            "created_time",
            "link",
            {"caption":{"text":True}})\
        	.changes(include_states=False)\
        	.run(conn)

    	#While "forever"
            while (yield feed.fetch_next()):
                new_gram = yield feed.next()
                for listener in listeners:
            	    listener.write_message(new_gram)
        except:
            pass


class WSocketHandler(tornado.websocket.WebSocketHandler):

    def check_origin(self, origin):
        return True

    def open(self):

        self.stream.set_nodelay(True)

        #Add to the user list
        listeners.add(self)

    def on_close(self):
        if self in listeners:
            listeners.remove(self)

if __name__ == '__main__':




  current_dir = os.path.dirname(os.path.abspath(__file__))
  public_folder = os.path.join(current_dir, 'public')
  tornado_app = tornado.web.Application([

    ('/', HomeHandler),
    (r'/echo', GramHandler),
    (r'/ws', WSocketHandler),
    (r'/filter(.*)', FilterPageHandler),
    (r'/public/(.*)', tornado.web.StaticFileHandler, { 'path': public_folder }),
    # ('.*', tornado.web.FallbackHandler, dict(fallback=wsgi_app)),

  ],
    cookie_secret=str(os.urandom(30))
  )
  server = tornado.httpserver.HTTPServer(tornado_app)
  server.listen(8000)
  tornado.ioloop.IOLoop.current().add_callback(emit_gram)
  tornado.ioloop.IOLoop.instance().start()
