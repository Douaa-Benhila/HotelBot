import sqlite3
import pandas as pd


csv_tables = {
    "TypesChambre_big.csv": "TypesChambre",
    "Hotels_big.csv": "Hotels",
    "Chambres_big.csv": "Chambres",
    "Clients_big.csv": "Clients",
    "Reservations_big.csv": "Reservations",
    "Occupations_big.csv": "Occupations",
}


conn = sqlite3.connect("hotels.db")
cursor = conn.cursor()

# Table Hotels
cursor.execute("""
CREATE TABLE IF NOT EXISTS Hotels (
    NumHo INTEGER PRIMARY KEY,
    NomHo TEXT NOT NULL,
    RueAdrHo TEXT NOT NULL,
    VilleHo TEXT NOT NULL,
    NbEtoilesHo INTEGER NOT NULL CHECK (NbEtoilesHo BETWEEN 1 AND 5)
);
""")

# Table TypesChambre
cursor.execute("""
CREATE TABLE IF NOT EXISTS TypesChambre (
    NumTy INTEGER PRIMARY KEY,
    NomTy TEXT NOT NULL,
    PrixTy REAL NOT NULL CHECK (PrixTy >= 0)
);
""")

# Table Chambres
cursor.execute("""
CREATE TABLE IF NOT EXISTS Chambres (
    NumCh INTEGER PRIMARY KEY,
    NumHo INTEGER NOT NULL,
    NumTy INTEGER NOT NULL,
    FOREIGN KEY (NumHo) REFERENCES Hotels(NumHo),
    FOREIGN KEY (NumTy) REFERENCES TypesChambre(NumTy)
);
""")

# Table Clients
cursor.execute("""
CREATE TABLE IF NOT EXISTS Clients (
    NumCl INTEGER PRIMARY KEY,
    NomCl TEXT NOT NULL,
    PrenomCl TEXT NOT NULL,
    RueAdrCl TEXT NOT NULL,
    VilleCl TEXT NOT NULL
);
""")

# Table Reservations
cursor.execute("""
CREATE TABLE IF NOT EXISTS Reservations (
    NumCl INTEGER NOT NULL,
    NumHo INTEGER NOT NULL,
    NumTy INTEGER NOT NULL,
    DateA TEXT NOT NULL,   -- format ISO : YYYY-MM-DD
    NbJours INTEGER NOT NULL CHECK (NbJours > 0),
    NbChambres INTEGER NOT NULL CHECK (NbChambres > 0),
    PRIMARY KEY (NumCl, NumHo, NumTy, DateA),
    FOREIGN KEY (NumCl) REFERENCES Clients(NumCl),
    FOREIGN KEY (NumHo) REFERENCES Hotels(NumHo),
    FOREIGN KEY (NumTy) REFERENCES TypesChambre(NumTy)
);
""")

# Table Occupations
cursor.execute("""
CREATE TABLE IF NOT EXISTS Occupations (
    NumCl INTEGER NOT NULL,
    NumHo INTEGER NOT NULL,
    NumCh INTEGER NOT NULL,
    DateA TEXT NOT NULL,  -- format ISO : YYYY-MM-DD
    DateD TEXT NOT NULL,  -- format ISO : YYYY-MM-DD
    CHECK (DateD > DateA),
    PRIMARY KEY (NumCl, NumHo, NumCh, DateA),
    FOREIGN KEY (NumCl) REFERENCES Clients(NumCl),
    FOREIGN KEY (NumHo) REFERENCES Hotels(NumHo),
    FOREIGN KEY (NumCh) REFERENCES Chambres(NumCh)
);
""")

# Trigger : vérifier qu’une réservation correspond bien à un type de chambre existant
cursor.execute("""
CREATE TRIGGER IF NOT EXISTS trg_check_reservation_insert
AFTER INSERT ON Reservations
FOR EACH ROW
BEGIN
    SELECT
      CASE
        WHEN NOT EXISTS (
            SELECT 1 FROM Chambres c
             WHERE c.NumHo = NEW.NumHo AND c.NumTy = NEW.NumTy
        )
        THEN RAISE(ABORT, 'PB C1 : pas de chambre de ce type dans cet hôtel, réservation impossible')
      END;
END;
""")

cursor.execute("""
CREATE TRIGGER IF NOT EXISTS trg_check_reservation_update
AFTER UPDATE OF NumHo, NumTy ON Reservations
FOR EACH ROW
BEGIN
    SELECT
      CASE
        WHEN NOT EXISTS (
            SELECT 1 FROM Chambres c
             WHERE c.NumHo = NEW.NumHo AND c.NumTy = NEW.NumTy
        )
        THEN RAISE(ABORT, 'PB C1 : modification impossible, ce type de chambre n’existe pas dans l’hôtel')
      END;
END;
""")


cursor.execute("""
CREATE TRIGGER IF NOT EXISTS trg_check_chambre_delete
AFTER DELETE ON Chambres
FOR EACH ROW
BEGIN
    SELECT
      CASE
        WHEN EXISTS (
            SELECT 1 FROM Reservations r
             WHERE r.NumHo = OLD.NumHo AND r.NumTy = OLD.NumTy
        )
        THEN RAISE(ABORT, 'PB C1 : suppression impossible, réservation encore présente pour ce type de chambre')
      END;
END;
""")


for csv_file, table in csv_tables.items():
    print(f"Importation de {csv_file} dans {table}...")
    df = pd.read_csv(csv_file)
    df.to_sql(table, conn, if_exists="append", index=False)


conn.commit()
conn.close()
print(" Base et tables créées avec succès (hotels.db).")
print(" Données importées avec succès dans hotels.db")


