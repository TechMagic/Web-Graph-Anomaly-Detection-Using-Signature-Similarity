import math
import sys

from scipy import spatial
import igraph
from igraph import *
import numpy as np
import os
import hashlib
import md5

import re


from os import listdir
from os.path import isfile, join

# The path to the data folder should be given as input
if len(sys.argv) != 2:
	print "Please provide input in this form: python anomaly.py <path to data folder>"
	sys.exit(1)

pathToDirectory = sys.argv[1]


def tryint(s):
    try:
        return int(s)
    except:
        return s

def alphanum_key(s):
    return [ tryint(c) for c in re.split('([0-9]+)', s) ]
    
    
def fetchGraphData(filename):

	#fetching the edge list and creating graphs

	graph = Graph(directed = True)

	f = open(filename, 'r')

	line = f.readline()
	line = line.split()

	graph.add_vertices(int(line[0]))

	# add the edges
	for row in f:
		edge = row.split(" ")
		graph.add_edges([(int(edge[0]),int(edge[1]))])
		
	f.close()

	return graph

def fetchFingerPrint(features):
	fingerPrint = []
	emptyFlag = True

	for key in features:
		if emptyFlag:
			fingerPrint = simHash(key, features[key])
			emptyFlag = False
		else:
			fingerPrint = [x+y for x, y in zip(fingerPrint, simHash(key, features[key]))]

	finalPrint = []

	for value in fingerPrint:
		if value >= 0:
			finalPrint.append(1)
		else:
			finalPrint.append(0)

	return finalPrint

def simHash(key, weight):
	hashValue = md5.new()
	hashValue.update(str(key))

	
	encodedValue = int(hashValue.hexdigest(),16)
	encodedValue = bin(encodedValue)[2:]

	weightList = []

	for i in encodedValue:
		if i == '0':
			weightList.append(-weight)
		else:
			weightList.append(weight)

	return weightList

def fetchSimilarity(g1, g2):

	#calculate similarity between two graphs using the hashed values
	similarity = 0.0

	for i in range(len(g1)):
		if g1[i] != g2[i]:
			similarity += 1.0

	return 1.0 - float(similarity/float(len(g1)))


def calculateAnomalies(domain):
	#fetch the files from the directory
	fullPath = str(pathToDirectory)+'/'+domain
	files = [f for f in listdir(fullPath) if isfile(join(fullPath, f))]
	files.sort(key=alphanum_key)
	print files

	#create graphs for each file
	graphList = []
	i = 0
	for f in files:
		i += 1
		graphList.append(fetchGraphData(fullPath+'/'+str(f)))


	#Pageranks for each graph
	pageranks = []
	for graph in graphList:
		pageranks.append(graph.pagerank())

	graphSignature = []
	

	#Get graph signature
	for i in range(len(graphList)):
		features = {}
		node = 0

		graph = graphList[i]
		adjacencyList = graph.get_adjlist(mode = OUT)
		pagerank = pageranks[i]



		# extract node features
		for j in graph.vs:
			features[j.index] = pagerank[node]
			node += 1


		# extract edge features
		for edge in graph.es:
			features[edge.index] = pagerank[edge.source] * (1.0 / len(adjacencyList[edge.source]))


		# get the finger print for the graph
		graphSignature.append(fetchFingerPrint(features))

	# fetch the similarity values for the hashed values
	similarity = [] 

	for i in range(len(graphSignature)-1):
		similarity.append(fetchSimilarity(graphSignature[i], graphSignature[i+1]))
	

	# write the similarity values to a file
	f = open(fullPath + "_time_series.txt", "w")

	for value in similarity:
		f.write(str(value) + "\n") 

	f.close()

	# calculate the moving range average
	movingAverage = 0.0

	for i in range(1,len(similarity)):
		movingAverage += abs(similarity[i] - similarity[i-1])

	movingAverage = float(movingAverage/float((len(similarity)-1)))
	

	#Calculating median
	median = np.median(similarity)


	#Calculating upper and lower treshold
	upperTreshold = float(median) + float(2*movingAverage)
	lowerTreshold = float(median) - float(2*movingAverage)
	
	print upperTreshold
	print lowerTreshold

	# Detect anomalies using upper and lower tresholds
	anomaly = []

	for i in range(0,len(similarity)-1):
		if similarity[i] < lowerTreshold or similarity[i+1] > upperTreshold:
			anomaly.append(i+1)

	print "The anomalies are: "
	for value in anomaly:
		print str(value) + "_" + domain + ".txt"

def main():
	domainlist = ['autonomous','enron_by_day','p2p-Gnutella','voices']

	for domain in domainlist:
		calculateAnomalies(domain)
	
if __name__ == "__main__":
    main()
