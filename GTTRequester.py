#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue Apr  2 22:43:53 2019

@author: Fabio Mazza
"""
import time,hashlib,requests
import sqlite3

class GTTRequester:
    secret = "759C97DC7D115966C30FD9169BB200D9"

    def __init__(self):
        #self.m = hashlib.md5()
        self.reqsess = requests.Session()
    
    def gentoken(self,requrl):
        m = hashlib.md5()
        timestamp = str(int(time.time()*1000))
        res = requrl.replace("http://www.5t.torino.it/proxyws", "")
        stringtobehashed = res+timestamp+self.secret
        m.update(stringtobehashed.encode('utf-8'))
        return m.hexdigest().lower(),timestamp
    def makeRequest(self,url):
        token,timestamp = self.gentoken(url)
        parametri = {
        "TOKEN" : token,
        "TIMESTAMP": timestamp,
        'User-Agent': 'okhttp/3.6.0',
        'Accept-Encoding': 'gzip',
        'Connection': 'Keep-Alive'
        }
        r = self.reqsess.get(url,headers=parametri)
        if(r.status_code == requests.codes.ok):
            return r.json()
        else:
            raise ValueError(str(r.status_code))
    def getArrivalTimes(self,stopid):
        res = "http://www.5t.torino.it/proxyws/ws2.1/rest/stops/{}/departures".format(stopid)
        
        return self.makeRequest(res)
    def getDetails(self,stopid):
        res = "http://www.5t.torino.it/proxyws/ws2.1/rest/stops/{}/branches/details".format(stopid)
        
        return self.makeRequest(res)
    def getAllStops(self):
        "http://www.5t.torino.it/proxyws/ws2.1/rest/stops/all"
        
import networkx as nx
import matplotlib.pyplot as plt
import matplotlib.cm as cm

class GTTBranch:
    def __init__(self,number,line,direction,stops):
        self.num = number
        self.line = line
        self.direction = direction
        self.stops = stops
    
class GTTNetCrawler:
    
    def __init__(self):
        self.graph = nx.MultiDiGraph()
        self.branches = dict()
        self.visited_stops = set()
        self.stops_tovisit = set()
        self.stops_failed = set()
        self.req = GTTRequester()
    
    def add_stop(self,stopnum):
        if(stopnum in self.visited_stops or stopnum in self.stops_failed):
            print("Stop {} already visited.".format(stopnum))
            return
        #if(stopnum in self.stops_tovisit):
        #    self.stops_tovisit.remove(stopnum)
        try:
            data = self.req.getDetails(stopnum)
        except ValueError as vale:
            print(vale.args)
            print("Request error, skipping stop {}".format(stopnum))
            self.stops_failed.add(stopnum)
            return
        self.visited_stops.add(stopnum)

        for el in data:
            branchid = el["branch"]
            if(branchid in self.branches.keys()):
                continue
            stops = list(map(int,el["branchDetail"]["stops"].split(",")))
            self.branches[branchid] = GTTBranch(branchid, el["lineName"],el["direction"],stops)
            for i in range(len(stops)):
                if(stops[i] not in self.visited_stops and stops[i] not in self.stops_failed):
                    self.stops_tovisit.add(stops[i])
                if(i>0):
                    #print(stops[i-1],stops[i])
                    self.graph.add_edge(stops[i-1],stops[i],key=branchid,branch=branchid)
    def startScanning(self,stopnum=""):
        if(stopnum != ""):
            self.stops_tovisit.add(stopnum)
        while(len(self.stops_tovisit)>0):
            stopnum = list(self.stops_tovisit)[0]
            print("Scanning stop {}, {} stops remaining ".format(stopnum,len(self.stops_tovisit)-1))
            self.stops_tovisit.remove(stopnum)
            self.add_stop(stopnum)

        
        print("No stop to scan")
        return
    def plotNetwork(self,drawf=nx.draw,cmfunct=cm.prism):
        f = plt.figure()
        b = self.branches.keys()
        edges,branches = zip(*nx.get_edge_attributes(self.graph,"branch").items())
        colors = tuple(map(cmfunct,branches))
        drawf(self.graph,edgelist=edges,edge_color = colors,node_size=20)
    def addStopCoordinates(self):
        stopsdat = self.req.makeRequest("http://www.5t.torino.it/proxyws/ws2.1/rest/stops/all")["stops"]
        latdict = dict()
        lngdict = dict()
        for el in stopsdat:
            try:
                stopid = int(el["id"])
            except ValueError:
                continue
            latdict[stopid] = float(el["lat"])
            lngdict[stopid] = float(el["lng"])
        nx.set_node_attributes(self.graph,latdict,"lat")
        nx.set_node_attributes(self.graph,lngdict,"long")
                
def plotnet(gttnet,drawf=nx.draw,cmfunct=cm.prism):
    f = plt.figure()
    b = gttnet.branches.keys()
    edges,branches = zip(*nx.get_edge_attributes(gttnet.graph,"branch").items())
    colors = tuple(map(cmfunct,branches))
    print(colors[1:7])
    drawf(gttnet.graph,edgelist=edges,edge_color = colors,node_size=20)
def addStopCoordinates(net):
        stopsdat = net.req.makeRequest("http://www.5t.torino.it/proxyws/ws2.1/rest/stops/all")["stops"]
        latdict = dict()
        lngdict = dict()
        for el in stopsdat:
            try:
                stopid = int(el["id"])
            except ValueError:
                continue
            latdict[stopid] = float(el["lat"])
            lngdict[stopid] = float(el["lng"])
        nx.set_node_attributes(net.graph,latdict,"lat")
        nx.set_node_attributes(net.graph,lngdict,"long")
#nx.write_gexf(gn.graph,"GTTMetwork")