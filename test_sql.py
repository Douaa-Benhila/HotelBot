import sqlite3

conn = sqlite3.connect("hotels.db")
cur = conn.cursor()

print("---- Hôtels à Paris ----")
for row in cur.execute("SELECT NumHo, NomHo, VilleHo, NbEtoilesHo FROM Hotels WHERE VilleHo = 'Paris' LIMIT 10;"):
    print(row)

print("\n---- Hôtels avec prix moyen <= 100 ----")
query = """
SELECT h.NumHo, h.NomHo, h.VilleHo, h.NbEtoilesHo,
       ROUND(AVG(t.PrixTy),2) AS prix_moyen
FROM Hotels h
JOIN Chambres ch ON ch.NumHo = h.NumHo
JOIN TypesChambre t ON t.NumTy = ch.NumTy
GROUP BY h.NumHo, h.NomHo, h.VilleHo, h.NbEtoilesHo
HAVING prix_moyen <= 100
LIMIT 10;
"""
for row in cur.execute(query):
    print(row)

conn.close()
