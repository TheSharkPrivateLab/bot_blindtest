#!/usr/bin/env python
# -*- coding: utf-8 -*-
import sqlite3
from random import shuffle, randint


class Database:
	"""
	Concerne toutes les fonctions relatives à la
	gestion de la base de données des animés
	"""

	def __init__(self, db_name):
		self.db_name = db_name
		self.msg = "id : {id}, anime: {name}, op: {op}, type: {type}, lien: <{link}>"
		conn = sqlite3.connect(self.db_name)
		cursor = conn.cursor()
		cursor.execute("""
		CREATE TABLE IF NOT EXISTS videos(
		id INTEGER PRIMARY KEY AUTOINCREMENT UNIQUE,
		name TEXT,
		lien TEXT,
		nb_op INTEGER,
		type INTEGER
		)""")
		conn.commit()
		cursor.execute("""
		CREATE TABLE IF NOT EXISTS categorie(
		id INTEGER PRIMARY KEY AUTOINCREMENT UNIQUE,
		ref TEXT
		)
		""")
		conn.commit()
		conn.close()

	def __len__(self):
		result = self.getall()
		return (len(result))

	def __repr__(self):
		return ("<Database> : %s object at %s" % (self.db_name, hex(id(self))))

	def __str__(self):
		return (self.db_name)

	def __call__(self):
		return (self.getall())

	def get_one(self, args):
		if (args is None):
			return (None)
		result = dict()
		conn = sqlite3.connect(self.db_name)
		cursor = conn.cursor()
		cursor.execute("SELECT ref FROM categorie WHERE id=?", (args[0],))
		temp_type = cursor.fetchone()
		conn.close()
		if (temp_type is None):
			temp_type = ('Unknow',)
		result["id"]   = args[0]
		result["type"] = temp_type[0]
		result["link"] = args[2]
		result["name"] = args[3]
		result["op"]   = args[4]
		return (result)

	def get_multiple(self, args):
		if (args is None):
			return (None)
		result = list()
		conn = sqlite3.connect(self.db_name)
		cursor = conn.cursor()
		for i in args:
			temp_result = dict()
			cursor.execute("SELECT ref FROM categorie WHERE id=?", (i[1],))
			temp_type = cursor.fetchone()
			if (temp_type is None):
				temp_type = "Unknow"
			temp_result["id"]   = i[0]
			temp_result["type"] = temp_type[0]
			temp_result["link"] = i[2]
			temp_result["name"] = i[3]
			temp_result["op"]   = i[4]
			result.append(temp_result)
		conn.close()
		return (tuple(result))

	def getcategorie(self):
		result = list()
		conn = sqlite3.connect(self.db_name)
		cursor = conn.cursor()
		cursor.execute("SELECT ref FROM categorie")
		temp = cursor.fetchall()
		conn.close()
		if len(temp) == 0:
			return None
		for i in temp:
			result.append(i[0])
		return tuple(result)

	def getone(self):
		conn = sqlite3.connect(self.db_name)
		cursor = conn.cursor()
		cursor.execute("""SELECT id, type, lien, name, nb_op FROM videos""")
		result = cursor.fetchone()
		conn.close()
		return (self.get_one(result))

	def getonefromid(self, id : int):
		conn = sqlite3.connect(self.db_name)
		cursor = conn.cursor()
		cursor.execute("""SELECT id, type, lien, name, nb_op FROM videos WHERE id=?""", (id,))
		result = cursor.fetchone()
		conn.close()
		return (self.get_one(result))

	def getall(self):
		conn = sqlite3.connect(self.db_name)
		cursor = conn.cursor()
		cursor.execute("""SELECT id, type, lien, name, nb_op FROM videos""")
		result = cursor.fetchall()
		conn.close()
		return (self.get_multiple(result))

	def addentry(self, name : str, op : int, link : str, types : str):
		conn = sqlite3.connect(self.db_name)
		cursor = conn.cursor()
		cursor.execute("SELECT id, type, lien, name, nb_op FROM videos WHERE lien=?", (link,))
		test = cursor.fetchone()
		if (test is not None):
			conn.close()
			print("Link already in the database :")
			return 1
		cursor.execute("SELECT id FROM categorie WHERE ref=?", (types,))
		test = cursor.fetchone()
		if (test is None):
			cursor.execute("INSERT INTO categorie(ref) VALUES(?)", (types,))
			conn.commit()
		cursor.execute("SELECT id FROM categorie WHERE ref=?", (types,))
		types = cursor.fetchone()[0]
		cursor.execute("INSERT INTO videos(name, lien, nb_op, type) VALUES(?, ?, ?, ?)", (name, link, op, types))
		conn.commit()
		conn.close()
		return 0

	def getrandom(self):
		length = self.getall()
		if (length is None):
			return 32
		ind = randint(1, len(length)) - 1
		one = length[ind]
		return (self.getonefromid(one['id']))

	def getallrandom(self):
		length = self.getall()
		if (length is None):
			return length
		length = list(length)
		shuffle(length)
		length = tuple(length)
		return (length)

	def deleteone(self, id : int):
		conn = sqlite3.connect(self.db_name)
		cursor = conn.cursor()
		cursor.execute("DELETE FROM videos WHERE id=?", (id,))
		conn.commit()
		conn.close()

	def getfromcategorie(self, categorie : str):
		conn = sqlite3.connect(self.db_name)
		cursor = conn.cursor()
		cursor.execute("SELECT id FROM categorie WHERE ref=?", (categorie))
		temp = cursor.fetchone()
		if (temp is None):
			conn.close()
			print("Unknow categorie : {}".format(categorie))
			return 16
		cursor.execute("SELECT id, type, lien, name, nb_op FROM videos WHERE type=?", temp)
		result = cursor.fetchall()
		conn.close()
		return (result)

	def getfromcategorierandom(self, categorie : str):
		result = list(self.getfromcategorie(categorie))
		shuffle(result)
		return (tuple(result))

	def printdbbyid(self, id : int):
		result = self.getonefromid(id)
		if (result is None):
			print("No entry at id {}.".format(id))
			return 64
		print(self.msg.format(**result))

	def printdb(self):
		result = self.getall()
		if (result is None):
			print("No entry.")
			return 32
		for i in result:
			print(self.msg.format(**i))

if (__name__ == '__main__'):
	my_ddb = Database('bdd.db')
	my_ddb.printdbbyid(21)
	my_ddb.addentry("Magi", 2, "https://www.youtube.com/watch?v=nGShsyMsfAg", "OST")
	my_ddb()
	my_ddb.printdbbyid(1)


# error : No entry at id   : 64
# error : No entry         : 32
# error : Unknow categorie : 16
# error :

# addentry(name, op, link, types)
# data = {"anime" : "Magi", "lien" : "ta mere", "nb_op" : 1, "type" : 1}
# cursor.execute("""
# INSERT INTO videos(anime, lien, nb_op, type) VALUES(:anime, :lien, :nb_op, :type)""", data)
# conn.commit()
# cursor.execute("""SELECT id, type, lien, anime, nb_op FROM videos""")
