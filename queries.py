# queries.py
# Requêtes SQL robustes. On ne joint TypesChambre que si on filtre par prix/type.
# Pour la dispo, on vérifie au niveau "chambre" (anti-chevauchement sur Occupations).

import sqlite3

DB_NAME = "hotels.db"

def connect():
    return sqlite3.connect(DB_NAME)

def villes_disponibles():
    conn = connect()
    cur = conn.cursor()
    cur.execute("SELECT DISTINCT VilleHo FROM Hotels ORDER BY VilleHo")
    rows = [r[0] for r in cur.fetchall()]
    conn.close()
    return ", ".join(rows)

def types_par_ville(ville: str):
    """
    Liste les types de chambres disponibles dans une ville avec prix min/moyen.
    """
    conn = connect()
    cur = conn.cursor()
    sql = """
        SELECT t.NomTy, ROUND(MIN(t.PrixTy),2) AS prix_min, ROUND(AVG(t.PrixTy),2) AS prix_moyen
        FROM Hotels h
        JOIN Chambres c ON c.NumHo = h.NumHo
        JOIN TypesChambre t ON t.NumTy = c.NumTy
        WHERE h.VilleHo = ?
        GROUP BY t.NomTy
        ORDER BY prix_min ASC
    """
    cur.execute(sql, (ville,))
    rows = cur.fetchall()
    conn.close()
    if not rows:
        return f"Aucun type trouvé à {ville}."
    return "Types de chambres à " + ville + " :\n" + "\n".join(
        [f"- {r[0]} : min ~{r[1]}€, moyen ~{r[2]}€" for r in rows]
    )

def prix_type_ville(ville: str, typeC: str):
    """
    Prix min/moyen d'un type de chambre donné dans une ville.
    """
    conn = connect()
    cur = conn.cursor()
    sql = """
        SELECT ROUND(MIN(t.PrixTy),2) AS prix_min, ROUND(AVG(t.PrixTy),2) AS prix_moyen
        FROM Hotels h
        JOIN Chambres c ON c.NumHo = h.NumHo
        JOIN TypesChambre t ON t.NumTy = c.NumTy
        WHERE h.VilleHo = ? AND LOWER(t.NomTy) = LOWER(?)
    """
    cur.execute(sql, (ville, typeC))
    row = cur.fetchone()
    conn.close()
    if not row or row[0] is None:
        return f"Aucun prix trouvé pour '{typeC}' à {ville}."
    return f"{typeC.capitalize()} à {ville} : min ~{row[0]}€, moyen ~{row[1]}€"

def recherche_complete(ville=None, prix=None, etoiles=None, stars_op=None, dateA=None, dateD=None, typeC=None):
    """
    Recherche combinée : ville, prix max (<=), étoiles (eq/ge/le), typeC, disponibilité (anti-chevauchement).
    - Si on a besoin du prix/type → join TypesChambre (t).
    - Si on vérifie la dispo → join Chambres (ch).
    - On retourne prix min (~) quand t est joint, sinon juste la liste.
    """
    conn = connect()
    cur = conn.cursor()

    need_t = bool(prix or typeC)           # besoin de TypesChambre ?
    need_ch = bool(dateA and dateD) or need_t  # besoin de Chambres si dates OU si t nécessaire

    conds, params = [], []

    # ----- SELECT & FROM -----
    if need_t:
        # on affiche aussi un prix min
        select_clause = "SELECT h.NomHo, h.VilleHo, h.NbEtoilesHo, MIN(t.PrixTy) AS prix"
    else:
        # pas de prix
        select_clause = "SELECT DISTINCT h.NomHo, h.VilleHo, h.NbEtoilesHo"

    query = select_clause + " FROM Hotels h"

    # ----- JOINS -----
    if need_ch:
        query += " JOIN Chambres ch ON ch.NumHo = h.NumHo"
    if need_t:
        query += " JOIN TypesChambre t ON t.NumTy = ch.NumTy"

    # ----- WHERE -----
    if ville:
        conds.append("h.VilleHo = ?")
        params.append(ville)

    if etoiles:
        if stars_op == 'ge':
            conds.append("h.NbEtoilesHo >= ?")
        elif stars_op == 'le':
            conds.append("h.NbEtoilesHo <= ?")
        else:
            conds.append("h.NbEtoilesHo = ?")
        params.append(etoiles)

    if prix and need_t:
        conds.append("t.PrixTy <= ?")
        params.append(prix)

    if typeC and need_t:
        conds.append("LOWER(t.NomTy) = LOWER(?)")
        params.append(typeC)

    if dateA and dateD:
        # anti-chevauchement au niveau chambre
        conds.append("""
            NOT EXISTS (
                SELECT 1 FROM Occupations o
                WHERE o.NumCh = ch.NumCh
                  AND o.DateA < ?
                  AND o.DateD > ?
            )
        """)
        params.extend([dateD, dateA])

    if conds:
        query += " WHERE " + " AND ".join(conds)

    # ----- GROUP BY / ORDER BY -----
    if need_t:
        query += " GROUP BY h.NomHo, h.VilleHo, h.NbEtoilesHo"
        query += " ORDER BY (prix IS NULL), prix ASC, h.NbEtoilesHo DESC, h.NomHo ASC"
    else:
        query += " ORDER BY h.NbEtoilesHo DESC, h.NomHo ASC"

    query += " LIMIT 50"

    # ----- EXEC -----
    try:
        cur.execute(query, params)
        rows = cur.fetchall()
    except Exception as e:
        conn.close()
        return f"⚠️ Erreur SQL: {e}"
    conn.close()

    if not rows:
        return "Aucun hôtel trouvé avec ces critères."

    # Formatage
    lines = []
    for r in rows:
        if need_t:
            nom, v, stars, prix_min = r
            line = f"{nom} ({stars}★) à {v}"
            if prix_min is not None:
                line += f" – dès ~{round(prix_min, 2)}€"
            lines.append(line)
        else:
            nom, v, stars = r
            lines.append(f"{nom} ({stars}★) à {v}")

    return "\n".join(lines)
