import re
import json
import random
import pickle
import numpy as np
import nltk
from nltk.stem.snowball import FrenchStemmer
import tensorflow as tf
from tensorflow.keras.models import load_model
from unidecode import unidecode
import tkinter as tk
from tkinter import scrolledtext
import extractors
import queries

try:
    nltk.data.find("tokenizers/punkt")
except LookupError:
    nltk.download("punkt")


##############prétraitement de texte de user ##############
stemmer = FrenchStemmer()


# --- NORMALISATION: DÉFINIE AVANT TOUT USAGE ---
def normalize_text(s: str) -> str:
    s = unidecode(s).lower()
    s = s.replace("\n", " ")
    s = re.sub(r"[^a-z0-9€\-'/ ]+", " ", s)
    s = re.sub(r"\s+", " ", s).strip()
    return s
#cleaning the sentences prétraitement 

def clean_up_sentences(sentence):
    sentence = normalize_text(sentence)      # << important
    tokens = nltk.word_tokenize(sentence)
    tokens = [stemmer.stem(w) for w in tokens]
    return tokens
# convert sentence to a bag of word , list of 0 and 1 that indicate if the world is there or not 

def bag_of_words(sentence):
    sentence_word=clean_up_sentences(sentence)
    bag=[0]*len(words)
    for w in sentence_word: 
        for i, word in enumerate(words):
            if word == w:
                bag[i] = 1 
    return np.array(bag)

# ==============================
# 2) Chargement du modèle + données
# ==============================
# Charge intents.json
with open('intents.json', encoding='utf-8') as f:
    intents = json.load(f)
# charger les fichiers pickle et mon modele
words=pickle.load(open('words.pkl','rb'))
classes=pickle.load(open('classes.pkl','rb'))
model = load_model('chatbot_model.h5')

# ==============================
# 3) Prédiction du tag
# ==============================
#predict function 
def predict_class(sentence):
    bow =bag_of_words(sentence)
    res = model.predict(np.array([bow]))[0]
    ERROR_THRESHOLD =0.25
    results = [[i, r] for i, r in enumerate(res) if r > ERROR_THRESHOLD]
    results. sort(key=lambda x: x[1], reverse=True)
    return_list=[]
    for r in results:
        return_list.append({'intent': classes[r[0]], 'probability': str(r[1])})
    return return_list

# ==============================
# 4) Génération de réponse
# ==============================

# ------ Réponse principale ------
def get_response(intents_list, intents_json, user_msg=""):
    if not intents_list:
        return "Je n’ai pas compris."

    tag = intents_list[0]['intent']

    # Intents classiques
    if tag in ["salutation", "merci", "au revoir", "aide", "nom_bot"]:
        for i in intents_json['intents']:
            if i['tag'] == tag:
                return random.choice(i['responses'])

    s = extractors.normalize_text(user_msg)

    # Demande: lister toutes les villes
    if "toutes les villes" in s or "villes disponibles" in s or re.search(r"\blister?\s+les\s+villes\b", s):
        return "Villes disponibles : " + queries.villes_disponibles()

    # Demande: lister types de chambres dans une ville
    if "types de chambres" in s or re.search(r"\btypes?\s+de\s+chambres?\b", s):
        ville = extractors.extract_city(user_msg)
        if not ville:
            return "Précisez la ville pour lister les types de chambres."
        return queries.types_par_ville(ville)

    # Demande: prix d'un type dans une ville (ex: prix d'une suite à Paris)
    if "prix" in s and ("suite" in s or "double" in s or "twin" in s or "single" in s):
        ville = extractors.extract_city(user_msg)
        typeC = extractors.extract_type(user_msg)
        if not typeC or not ville:
            # si pas complet, on bascule en recherche complète générique
            crit = extractors.extract_all(user_msg)
            return queries.recherche_complete(**crit)
        return queries.prix_type_ville(ville, typeC)

    # Intent générique de recherche
    if tag.startswith("recherche"):
        crit = extractors.extract_all(user_msg)
        return queries.recherche_complete(**crit)

    # Fallback: réponse d'intent
    for i in intents_json['intents']:
        if i['tag'] == tag:
            return random.choice(i['responses'])
    return "Je n’ai pas compris."


print("BOT is running")


"""while True:
    message = input("Vous: ")
    ints = predict_class(message)
    res = get_response(ints, intents)
    print(res)
"""
# ==============================
# 5) Interface Tkinter
# ==============================
APP_TITLE = "Chatbot Hôtel"

def insert_chat(sender: str, text: str):
    """
    Insère un message formaté dans la zone de chat (lecture seule).
    """
    chat_window.config(state="normal")
    chat_window.insert(tk.END, f"{sender}: {text}\n")
    chat_window.config(state="disabled")
    chat_window.see(tk.END)

def send_message(event=None):
    """
    Récupère le texte utilisateur, appelle le modèle et affiche la réponse.
    """
    user_msg = entry.get().strip()
    if not user_msg:
        return

    # Afficher message utilisateur
    insert_chat("Vous", user_msg)
    entry.delete(0, tk.END)

    # Prédire et répondre
    try:
        ints = predict_class(user_msg)
        bot_msg = get_response(ints, intents, user_msg)
    except Exception as e:
        bot_msg = f"⚠️ Erreur: {e}"

    insert_chat("Bot", bot_msg)

def on_return(event):
    """
    Entrée = envoyer (empêche l’insertion d’un '\n' dans l’Entry).
    """
    send_message()
    return "break"

# Fenêtre principale
root = tk.Tk()
root.title(APP_TITLE)
root.geometry("560x560")
root.minsize(420, 420)

# Titre
header = tk.Label(root, text=APP_TITLE, anchor="w",
                  padx=12, pady=8, font=("Segoe UI", 12, "bold"))
header.pack(fill=tk.X)

# Zone de conversation (lecture seule)
chat_window = scrolledtext.ScrolledText(root, wrap=tk.WORD, state="disabled",
                                        font=("Segoe UI", 10))
chat_window.pack(padx=10, pady=10, fill=tk.BOTH, expand=True)

# Zone d’entrée + bouton
entry_frame = tk.Frame(root)
entry_frame.pack(fill=tk.X, padx=10, pady=(0, 10))

entry = tk.Entry(entry_frame, font=("Segoe UI", 10))
entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 10))
entry.focus_set()

send_btn = tk.Button(entry_frame, text="Envoyer", width=10, command=send_message)
send_btn.pack(side=tk.RIGHT)

# Raccourcis clavier
root.bind("<Return>", on_return)
root.bind("<KP_Enter>", on_return)

# Message d’accueil
insert_chat("Bot", "Bonjour 👋 ! Je suis votre assistant. Écrivez un message pour commencer.")

# Boucle Tkinter
root.mainloop()
