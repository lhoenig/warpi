#!/usr/bin/env python

import sqlite3
import json
import geo

conn = sqlite3.connect("warpi.db")
c = conn.cursor()

ssids = []
networks = []

# first get all unique network ssids
c.execute("SELECT DISTINCT ssid FROM wifi_data")
while True:
	res = c.fetchone()
	if res is None:
		break
	res = res[0]
	ssids.append(res)

for ssid in ssids:
	# get center point for network
	c.execute("SELECT * FROM wifi_data WHERE ssid IS \"" + ssid + "\" ORDER BY signal DESC LIMIT 1")
	strongest = c.fetchone()
	c.execute("SELECT * FROM geodata WHERE wifi_data_key IS " + `strongest[0]`)
	strongest_geodata = c.fetchone()

	# todo: implement better algo for weakest signal
	c.execute("SELECT * FROM wifi_data WHERE ssid IS \"" + ssid + "\" ORDER BY signal ASC LIMIT 1")
	weakest = c.fetchone()
	c.execute("SELECT * FROM geodata WHERE wifi_data_key IS " + `weakest[0]`)
	weakest_geodata = c.fetchone()

	# calculate radius
	geo_strongest = geo.xyz(float(strongest_geodata[1]), float(strongest_geodata[2]))
	geo_weakest = geo.xyz(float(weakest_geodata[1]), float(weakest_geodata[2]))
	radius = geo.distance(geo_strongest, geo_weakest)

	networks.append({"ssid": ssid, 
									 "center_lat": strongest_geodata[1], 
									 "center_lon": strongest_geodata[2], 
									 "radius": radius, 
									 "max_quality": strongest[3],
									 "frequency": strongest[4],
									 "bitrates": strongest[5],
									 "encrypted": strongest[6],
									 "encryption_type": strongest[7],
									 "channel": strongest[8],
									 "address": strongest[9],
									 "mode": strongest[10]})

#print networks

conn.close()

with open("wifi.json", "w") as outfile:
	json.dump(networks, outfile, indent = 4, sort_keys = True)
	outfile.close()