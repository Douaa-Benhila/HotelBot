# extractors.py
# Extraction robuste: ville, prix, étoiles (avec au moins/au plus), dates (JJ/MM/AAAA ou texte),
# type de chambre (single/double/twin/suite). Tolère accents et petites fautes.

import re
import sqlite3
from unidecode import unidecode
from datetime import datetime, timedelta

DB_NAME = "hotels.db"

# ----------------------------
# Normalisation légère
# ----------------------------
def normalize_text(s: str) -> str:
    return unidecode(s).lower().strip()

# ----------------------------
# 1) VILLE (matching sur DB)
# ----------------------------
def extract_city(msg: str):
    """
    Retourne une ville existante en DB si elle est mentionnée (insensible aux accents/casse).
    """
    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()
    cur.execute("SELECT DISTINCT VilleHo FROM Hotels")
    villes_raw = [r[0] for r in cur.fetchall()]
    conn.close()

    s = normalize_text(msg)
    # Dictionnaire {forme_normalisee: forme_originale}
    villes_norm = { normalize_text(v): v for v in villes_raw }
    for v_norm, v_orig in villes_norm.items():
        if v_norm in s:
            return v_orig  # on renvoie l'original (capitalisé comme en DB)
    return None

# ----------------------------
# 2) PRIX (<= X)
# ----------------------------
def extract_price(msg: str):
    """
    Capture un plafond de prix si présent (100€, <120, max 200, moins de 80 euro).
    Retourne un int (plafond) ou None.
    """
    s = normalize_text(msg)

    # cas "moins de 120", "max 200", "<= 150", "<120"
    if re.search(r"(moins|sous|max|<=|=<|<|inferieur|inf)", s):
        m = re.search(r"(\d{2,4})", s)
        if m: return int(m.group(1))

    # cas "100€", "100 euros"
    m2 = re.search(r"(\d{2,4})\s*(€|euros?)", s)
    if m2: return int(m2.group(1))

    return None

# ----------------------------
# 3) ETOILES (avec bornes)
# ----------------------------
def extract_stars_with_bound(msg: str):
    """
    Renvoie (value, op) où op ∈ {'eq','ge','le'} :
      - "au moins 3 etoiles" -> (3, 'ge')
      - "au plus 2 etoiles"  -> (2, 'le')
      - "3 etoiles", "****"  -> (3/4, 'eq')
    """
    s = normalize_text(msg)

    # étoiles avec texte "au moins/au plus"
    m = re.search(r"au\s+moins\s+(\d)\s*etoiles?", s)
    if m: return int(m.group(1)), 'ge'
    m = re.search(r"(au\s+plus|max)\s+(\d)\s*etoiles?", s)
    if m: return int(m.group(2)), 'le'

    # "3 etoiles"
    m = re.search(r"(\d)\s*etoiles?", s)
    if m: return int(m.group(1)), 'eq'

    # "****" ou "★★★★★"
    stars_ascii = re.findall(r"(\*{1,5})", s)
    if stars_ascii:
        return len(stars_ascii[0]), 'eq'
    stars_unicode = re.findall(r"(★{1,5})", s)
    if stars_unicode:
        return len(stars_unicode[0]), 'eq'

    return None, None

def extract_stars(msg: str):
    v, op = extract_stars_with_bound(msg)
    return v

def extract_stars_op(msg: str):
    v, op = extract_stars_with_bound(msg)
    return op

# ----------------------------
# 4) TYPE de chambre
# ----------------------------
def extract_type(msg: str):
    s = normalize_text(msg)
    # tolérance fautes courantes
    synonyms = {
        "single": ["single", "simple"],
        "double": ["double", "dbl", "chambre double", "double room"],
        "twin":   ["twin"],
        "suite":  ["suite", "suitt", "suitye", "suiets"]
    }
    for canon, forms in synonyms.items():
        for f in forms:
            if f in s:
                return canon
    return None

# ----------------------------
# 5) DATES (JJ/MM/AAAA & texte FR)
# ----------------------------
FR_MONTHS = {
    "janvier":1,"fevrier":2,"février":2,"mars":3,"avril":4,"mai":5,"juin":6,
    "juillet":7,"aout":8,"août":8,"septembre":9,"octobre":10,"novembre":11,
    "decembre":12,"décembre":12
}

def _parse_fr_date_token(tok: str, default_year=None):
    tok = normalize_text(tok)
    # 17/11/2025
    m = re.match(r"^(\d{1,2})/(\d{1,2})/(\d{4})$", tok)
    if m:
        j, mo, an = int(m.group(1)), int(m.group(2)), int(m.group(3))
        return datetime(an, mo, j).date()

    # 17/11 (année par défaut = année courante)
    m2 = re.match(r"^(\d{1,2})/(\d{1,2})$", tok)
    if m2:
        j, mo = int(m2.group(1)), int(m2.group(2))
        an = default_year or datetime.now().year
        return datetime(an, mo, j).date()

    # 17 novembre (optionnellement 2025)
    m3 = re.match(r"^(\d{1,2})\s+([a-zéèêàùôûîïç\-]+)(?:\s+(\d{4}))?$", tok)
    if m3:
        j = int(m3.group(1))
        mois_txt = m3.group(2)
        mo = FR_MONTHS.get(mois_txt)
        if not mo: return None
        an = int(m3.group(3)) if m3.group(3) else (default_year or datetime.now().year)
        return datetime(an, mo, j).date()

    return None

def extract_dates(msg: str):
    """
    Retourne (dateA_iso, dateD_iso) ou (None, None).
    Gère: "demain", "aujourd'hui", "le 17/11/2025", "du 5 decembre au 7 decembre 2025",
         "entre 01/01/2026 et 03/01/2026".
    """
    s = normalize_text(msg)

    # aujourd'hui
    if "aujourd" in s:
        d1 = datetime.today().date()
        d2 = d1 + timedelta(days=1)
        return d1.isoformat(), d2.isoformat()

    # demain
    if "demain" in s:
        d1 = datetime.today().date() + timedelta(days=1)
        d2 = d1 + timedelta(days=1)
        return d1.isoformat(), d2.isoformat()

    # du/entre ... au/et ...
    m_range = re.search(r"(du|entre)\s+(.+?)\s+(au|et|a)\s+(.+)$", s)
    if m_range:
        left, right = m_range.group(2).strip(), m_range.group(4).strip()
        d1 = _parse_fr_date_token(left, default_year=datetime.now().year)
        d2 = _parse_fr_date_token(right, default_year=datetime.now().year)
        if d1 and d2 and d2 > d1:
            return d1.isoformat(), d2.isoformat()

    # le 17/11/2025  ou  le 17 novembre (séjour 1 nuit)
    m_one = re.search(r"\ble\s+(.+)$", s)
    if m_one:
        tok = m_one.group(1).strip()
        d1 = _parse_fr_date_token(tok, default_year=datetime.now().year)
        if d1:
            return d1.isoformat(), (d1 + timedelta(days=1)).isoformat()

    # format simple "17/11/2025" dans le message sans "le"
    m_dmY = re.search(r"(\d{1,2}/\d{1,2}/\d{4})", s)
    if m_dmY:
        try:
            d1 = datetime.strptime(m_dmY.group(1), "%d/%m/%Y").date()
            return d1.isoformat(), (d1 + timedelta(days=1)).isoformat()
        except:
            pass

    return None, None

# ----------------------------
# 6) Extraction globale
# ----------------------------
def extract_all(msg: str):
    dA, dD = extract_dates(msg)
    stars_val, stars_op = extract_stars_with_bound(msg)
    return {
        "ville":     extract_city(msg),
        "prix":      extract_price(msg),
        "etoiles":   stars_val,
        "stars_op":  stars_op,       # 'eq' | 'ge' | 'le' | None
        "dateA":     dA,
        "dateD":     dD,
        "typeC":     extract_type(msg)
    }
