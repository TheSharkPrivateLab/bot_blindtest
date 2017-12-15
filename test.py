import sqlite3


class anime:
	"""
	concerne toutes les fonctions relatibes à la
	gestion de la base de données des animés
	"""

	def __init__(self, db_name):
		self.db_name = db_name
		conn = sqlite3.connect(self.db_name)
		cursor = conn.cursor()
		cursor.execute("""
		CREATE TABLE IF NOT EXISTS videos(
		id INTEGER PRIMARY KEY AUTOINCREMENT UNIQUE,
		anime TEXT,
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
		cursor.execute("""SELECT id, type, lien, anime, nb_op FROM videos""")
		result = cursor.fetchall()
		conn.close()
		return (len(result))

	def __str__(self):
		return (self.db_name)

	def __call__(self):
		return (self.printdb())

	def getone(self):
		conn = sqlite3.connect(self.db_name)
		cursor = conn.cursor()
		cursor.execute("""SELECT id, type, lien, anime, nb_op FROM videos""")
		result = cursor.fetchone()
		conn.close()
		return (result)

	def getall(self):
		conn = sqlite3.connect(self.db_name)
		cursor = conn.cursor()
		cursor.execute("""SELECT id, type, lien, anime, nb_op FROM videos""")
		result = cursor.fetchall()
		conn.close()
		return (result)

	def addentry(self, anime : str, op : int, link : str, types : int):
		conn = sqlite3.connect(self.db_name)
		cursor = conn.cursor()
		cursor.execute("INSERT INTO videos(anime, lien, nb_op, type) VALUES(?, ?, ?, ?)", (anime, link, op, types))
		conn.commit()
		conn.close()

	def getrandom(self):
		#randint()
		pass

	def deleteone(self, id : int):
		conn = sqlite3.connect(self.db_name)
		cursor = conn.cursor()
		cursor.execute("DELETE FROM videos WHERE id=?", (id,))
		conn.commit()
		conn.close()

	def printdb(self):
		conn = sqlite3.connect(self.db_name)
		cursor = conn.cursor()
		cursor.execute("""SELECT id, type, lien, anime, nb_op FROM videos""")
		result = cursor.fetchall()
		if (len(result) == 0):
			print("No entry.")
		for i in result:
			print("id : {0[0]}, anime: {0[3]}, op: {0[4]}, type: {0[1]}, type: {0[2]}".format(i))
			conn.close()

my_ddb = anime('bdd.db')
my_ddb.deleteone(44)
my_ddb()

# data = {"anime" : "Magi", "lien" : "ta mere", "nb_op" : 1, "type" : 1}
# cursor.execute("""
# INSERT INTO videos(anime, lien, nb_op, type) VALUES(:anime, :lien, :nb_op, :type)""", data)
# conn.commit()
# cursor.execute("""SELECT id, type, lien, anime, nb_op FROM videos""")
