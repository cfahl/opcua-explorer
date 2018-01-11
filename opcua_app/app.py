import opcua
import socket
import threading
import sqlite3
import csv
import time
import datetime
from threading import Timer,Thread
from sqlite3 import Error
from flask import Flask, request
from flask_restful import Resource, Api
from sqlalchemy import create_engine
from opcua import ua, uamethod, Server, Client

# creating an engine to connect to SQLite3
# the watchlist.db is in app root folder
sql_engine = create_engine('sqlite:///watchlist.db')

app = Flask(__name__)
app.config['PROPAGATE_EXCEPTIONS'] = True
api = Api(app)

server = Server()

def polling():
    """ polling the tags table inserting into tagshistory table every x amount of time"""
    next_call = time.time()
    is_int = True
    while(True):
        try:
            conn = sql_engine.connect()
            data = conn.execute("SELECT * FROM tags")
            for i in data.fetchall():
                try:
                    value = int(i[2])
                    is_int = True
                except ValueError:
                    is_int = False
                if is_int:
                    conn.execute("INSERT OR IGNORE INTO taghistory (timestamp, tag_name, value_int, value_str) VALUES (?, ?, ?, ?)", (datetime.datetime.now(), i[1], i[2], ""))
                else:
                    conn.execute("INSERT OR IGNORE INTO taghistory (timestamp, tag_name, value_int, value_str) VALUES (?, ?, ?, ?)", (datetime.datetime.now(), i[1], "", i[2]))
        except Error as e:
            print(e)
        next_call = next_call + 15 # a later change is to recieve the poll rate from the configuration, or change to more appropriate value
        time.sleep(next_call - time.time())

polling_thread = threading.Thread(target=polling)
polling_thread.start()


def clean_taghistory():
    """ cleaning the taghistory table, anything with a timestamp older than 24 hours gets deleted, checks every x amount of time """
    next_call = time.time()
    while True:
        try:
            conn = sql_engine.connect()
            clean = conn.execute("DELETE FROM taghistory WHERE timestamp <= datetime('now','-1 day')")
        except Error as e:
            print(e)
        next_call = next_call + 120
        time.sleep(next_call - time.time())

cleaning_thread = threading.Thread(target=clean_taghistory)
cleaning_thread.start()


def populate_server(myobj):
    """ This function is to populate server with dummy test values """
    i = 0
    while (i < 50):
        myvar = myobj.add_variable(1, "Tag" + str(i), i)
        i += 1
        myvar.set_writable()
    return myobj

def start_server():
    """ This function is to spool up an opcua server """
    server.set_endpoint("opc.tcp://0.0.0.0:4840/freeopcua/server/")
    objects = server.get_objects_node()
    myobj = objects.add_object(0, "MyObject")
    populate_server(myobj)
    server.start()

def stop_server():
    server.stop()
    click.echo('server stopped')

""" starts the server and creates client and node objects """
start_server()
client = Client("opc.tcp://0.0.0.0:4840/freeopcua/server/")
client.connect()
myobj = client.get_objects_node()

class TagListValue(Resource):
    """ This class is responsible for the tag list of values found within opcua """
    def get(self, arg):
        """This will list the tags values within opcua server """
        if arg == 'all':
            """ If the argument is all, all values will be displayed """
            tag_list = get_all_tags(myobj.get_children(), 'value')
            return tag_list
        else:
            """ If a range is specified then only the tags values in range specifed x:y will be displayed """
            range_list = []
            tag_list = get_all_tags(myobj.get_children(), 'value')
            try:
                x,y = arg.split(":")
                if int(y) > len(tag_list):
                    y = len(tag_list)
                for i in range(int(x),int(y)):
                    range_list.append(tag_list[i])
                return range_list
            except Error as e:
                return "Range is not in correct format, please try x:y"

class TagListName(Resource):
    """ This class is responsible for the tag list of names found within opcua """
    def get(self, arg):
        """ This will list the names of the tags within opcua server """
        if arg == 'all':
            """ If the argument is all, all names will be displayed i.e Tag1, Tag2 """
            tag_list = get_all_tags(myobj.get_children(), 'name')
            return tag_list
        else:
            """ If a range is specified then only the tags names in range specified x:y will be displayed """
            range_list = []
            tag_list = get_all_tags(myobj.get_children(), 'name')
            try:
                x,y = arg.split(":")
                if int(y) > len(tag_list):
                    y = len(tag_list)
                for i in range(int(x),int(y)):
                    range_list.append(tag_list[i])
                return range_list
            except Error as e:
                return "Range is not in correct format, please try x:y"

class TagValue(Resource):
    """ This class is responsible for finding a specific value within the tag list """
    def get(self, arg):
        """ This will provide the user with the value for a specified tag, searching by tag name, ie Tag1 """
        tag_dict = {}
        value_list = get_all_tags(myobj.get_children(), 'value')
        name_list = get_all_tags(myobj.get_children(), 'name')
        tag_dict = dict(zip(name_list, value_list))
        try:
            value = tag_dict[arg]
            return value
        except KeyError:
            return "Tag does not exist"

def get_all_tags(nodes, value_type):
    """ This helper method is used to get all of the tags from the opcua server and returns a list """
    tag_list = []
    for node in nodes:
        child_nodes = node.get_children()
        if child_nodes:
            if value_type == 'value':
                tag_list.extend(get_all_tags(child_nodes, 'value'))
            elif value_type == 'name':
                tag_list.extend(get_all_tags(child_nodes, 'name'))
        else:
            string_node = str(node)
            string_node = string_node[string_node.find('ns='):string_node.find('))')]
            if string_node and string_node != ',':
                if value_type == 'value':
                    value = node.get_value()
                elif value_type == 'name':
                    value = node.get_browse_name()
                    value = str(value)
                    value = value[value.find(':') + 1:value.find(')')]
                tag_list.append(value)
    return tag_list

def get_node(path, name_space, client):
    """ This helper method returns a specified node """
    if name_space:
        path_formatted = 'ns={};i={}'.format(name_space, path)
        n = client.get_node(path_formatted)
        return n

class Watchlist(Resource):
    """ This class is responsible for adding, listing, deleting tags from the watchlist as well as exporting the watchlist to a csv file """
    def put(self, arg):
        """ This method puts rows into the watchlist database, specifically the tags table at the moment """
        try:
            conn = sql_engine.connect()
            tag1, tag2, tag3 = str(arg), str(arg), str(arg)
            node_id = tag1[tag1.find('nodeid=') + 7:tag1.find('tag_name')]
            tag_name = tag2[tag2.find('tag_name=') + 9:tag2.find('value')]
            value = tag3[tag3.find('value=') + 6:]
            tag = (node_id, tag_name, value)
            find = conn.execute("SELECT 1 FROM tags WHERE tag_name=?",(tag_name,)).fetchone()
            if find:
                return ("Tag with " + tag_name + " already exists in tags table, please change the tag name")
            else:
                conn.execute("INSERT INTO tags(nodeid, tag_name, value) VALUES(?, ?, ?)",(tag))
                return (tag, " has been added to the tags table in the watchlist database")
        except Error as error:
            print(error)
            return error

    def get(self, arg="all"):
        """ This method gets all the data within the tags table and displays """
        if arg == "all":
            try:
                conn = sql_engine.connect()
                query = conn.execute("SELECT * FROM tags")
                result = {'tags': [dict(zip(tuple (query.keys()), i)) for i in query.cursor]}
                self.export_to_csv(query)
                return result
            except Error as error:
                print(error)
                return error
        else:
            try:
                conn = sql_engine.connect()
                query = conn.execute("SELECT * FROM tags WHERE tag_name=?",(arg,))
                result = {'tag': [dict(zip(tuple (query.keys()), i)) for i in query.cursor]}
                self.export_to_csv(query)
                return result
            except Error as error:
                print(error)
                return error


    def delete(self, arg):
        """ This method deletes specified row from the tags table, key is TAG NAME"""
        try:
            conn = sql_engine.connect()
            find = conn.execute("SELECT 1 FROM tags WHERE tag_name=?",(arg,)).fetchone()
            if find:
                delete = conn.execute("DELETE FROM tags WHERE tag_name=?",(arg,))
                return (arg + " deleted") 
            else:
                return (arg + " does not exist in the database")
        except Error as error:
            print(error)
            return error

    def validate_tag():
        """ method to validate the tag that is to be inserted into the wathlist is an actual tag and values are correct """
        pass

    def export_to_csv(self, rows):
        """ This method is responsible for exporting the tags table into a watchlist.csv """
        write_dir = "/opt/sightmachine/data-tools/de-toolbox/opcua/app/watchlist.csv"
        # need to fix the writing, nothing is being written, but have tested it is the correct location
        with open(write_dir, 'w') as f:
            # add headers and use a dictionary to write to csv
            writer = csv.writer(f, delimiter=',')
            writer.writerow(rows)
        f.close()

class TagHistory(Resource):
    """ This class is responsible for polling from the watchlist and updating the tag history table in the database """
    def get(self, arg="all"):
        """ This method gets all the data within the tags table and displays """
        if arg == "all":
            try:
                conn = sql_engine.connect()
                query = conn.execute("SELECT * FROM taghistory")
                result = {'tags': [dict(zip(tuple (query.keys()), i)) for i in query.cursor]}
                return result
            except Error as error:
                print(error)
                return error
        else:
            # just get now and last x amount of time
            try:
                conn = sql_engine.connect()
                query = conn.execute("SELECT * FROM taghistory WHERE tag_name=?",(arg,))
                result = {'tags': [dict(zip(tuple (query.keys()), i)) for i in query.cursor]}
                return result
            except Error as error:
                print(error)
                return error

    def delete(self, arg):
        try: 
            conn = sql_engine.connect()
        except Error as error:
            print(error)
            return error
        if arg == "all":
            delete = conn.execute("DELETE FROM taghistory")
        else:
            #time_range = '-' + str(arg) + ' minutes'
            delete = conn.execute("DELETE FROM taghistory WHERE timestamp<= datetime('now', '-5 minutes')")



api.add_resource(TagListValue, '/tags/listvalue/<string:arg>')
api.add_resource(TagListName, '/tags/listname/<string:arg>')
api.add_resource(TagValue, '/tags/value/<string:arg>')
api.add_resource(Watchlist, '/watchlist/<string:arg>')
api.add_resource(TagHistory, '/taghistory/<string:arg>')


if __name__ == '__main__':
    app.run(threaded = True)

