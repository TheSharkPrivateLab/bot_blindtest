import sqlite3


class Database:
	"""
	concerne toutes les fonction relatif a la
	gestion de la base de donnée des animé
	"""

	def __init__(self, db_name):
		self.db_name = db_name
		self.msg = "id : {0[0]}, anime: {0[3]}, op: {0[4]}, type: {0[1]}, lien: {0[2]}"
		conn = sqlite3.connect(self.db_name)
		cursor = conn.cursor()
		cursor.execute("""
		CREATE TABLE IF NOT EXISTS videos(
		id INTEGER PRIMARY KEY AUTOINCREMENT UNIQUE,
		name TEXT,
		lien TEXT,
		nb_op INTEGER,
		type INTEGER
		)
		""")
		conn.commit()
		conn.close()

	def __len__(self):
		conn = sqlite3.connect(self.db_name)
		cursor = conn.cursor()
		cursor.execute("""SELECT id, type, lien, name, nb_op FROM videos""")
		result = cursor.fetchall()
		conn.close()
		return (len(result))

	def __repr__(self):
		return ("<Database> : %s object at %s" % (self.db_name, hex(id(self))))

	def __str__(self):
		return (self.db_name)

	def __call__(self):
		return (self.printdb())

	def __getfromtypeid(self,):
		pass

	def getone(self):
		conn = sqlite3.connect(self.db_name)
		cursor = conn.cursor()
		cursor.execute("""SELECT id, type, lien, name, nb_op FROM videos""")
		result = cursor.fetchone()
		conn.close()
		return (result)

	def getonefromid(self, id : int):
		conn = sqlite3.connect(self.db_name)
		cursor = conn.cursor()
		cursor.execute("""SELECT id, type, lien, name, nb_op FROM videos WHERE id=?""", (id,))
		result = cursor.fetchone()
		conn.close()
		return (result)

	def getall(self):
		conn = sqlite3.connect(self.db_name)
		cursor = conn.cursor()
		cursor.execute("""SELECT id, type, lien, name, nb_op FROM videos""")
		result = cursor.fetchall()
		conn.close()
		return (result)

	def addentry(self, name : str, op : int, link : str, types : int):
		conn = sqlite3.connect(self.db_name)
		cursor = conn.cursor()
		cursor.execute("SELECT id, type, lien, name, nb_op FROM videos WHERE lien=?", (link,))
		test = cursor.fetchone()
		if (test is not None):
			conn.close()
			print("Link already in the database :")
			print(self.msg.format(test))
			return
		cursor.execute("INSERT INTO videos(name, lien, nb_op, type) VALUES(?, ?, ?, ?)", (name, link, op, types))
		conn.commit()
		conn.close()

	def getrandom(self):
		length = self.getall()
		if (len(length) == 0):
			return
		return (self.getonefromid(randint(1, len(length))))

	def deleteone(self, id : int):
		conn = sqlite3.connect(self.db_name)
		cursor = conn.cursor()
		cursor.execute("DELETE FROM videos WHERE id=?", (id,))
		conn.commit()
		conn.close()

	def printdbbyid(self, id : int):
		result = self.getonefromid(id)
		if (result is None):
			print("No entry at id {}.".format(id))
			return
		print(self.msg.format(result))

	def printdb(self):
		result = self.getall()
		if (len(result) == 0):
			print("No entry.")
			return
		for i in result:
			print(self.msg.format(i))

if (__name__ == '__main__'):
	my_ddb = Database('bdd.db')
	my_ddb.printdbbyid(21)
	my_ddb.addentry("Magi", 2, "https://www.youtube.com/watch?v=nGShsyMsfAg", 1)
	my_ddb()


# addentry(name, op, link, types)
# data = {"anime" : "Magi", "lien" : "ta mere", "nb_op" : 1, "type" : 1}
# cursor.execute("""
# INSERT INTO videos(anime, lien, nb_op, type) VALUES(:anime, :lien, :nb_op, :type)""", data)
# conn.commit()
# cursor.execute("""SELECT id, type, lien, anime, nb_op FROM videos""")
