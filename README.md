# HotelBot : chatbot intelligent pour la réservation hôtelière
Chatbot en français qui comprend une demande en langage naturel (ville, dates, budget, étoiles, type de chambre) et interroge une base de données SQLite pour proposer les hôtels disponibles.

## Table des matières

- [Informations générales](#informations-générales)
- [Prérequis](#prérequis)
- [Installation et utilisation](#installation-et-utilisation)
- [Technologies utilisées](#technologies-utilisées)
- [Bugs connus et limites](#bugs-connus-et-limites)
- [Auteurs](#auteurs)

## Informations générales

HotelBot reconnaît l'intention de l'utilisateur grâce à un réseau de neurones, puis extrait les critères de la phrase :

- **ville** (ex. « Paris »)
- **budget** (« moins de 120€ », « max 100€ »)
- **nombre d'étoiles** (exact, au moins, au plus)
- **type de chambre** (single, double, twin, suite)
- **dates** (`JJ/MM/AAAA`, « demain », « du 5 décembre au 7 décembre »)

Ces critères sont traduits en requêtes SQL pour lister les hôtels, leurs prix, les types de chambres et la disponibilité sur une période. Une interface graphique de type messagerie est fournie.

**Exemple :**

> Je veux un hôtel à Paris avec au moins 3 étoiles, moins de 150€, entre le 13/11/2025 et le 15/11/2025

## Prérequis

- Python ≥ 3.9
- SQLite3 (inclus par défaut avec Python)

## Installation et utilisation

**1. Installer les dépendances** (un environnement virtuel est recommandé) :

```bash
pip install numpy nltk unidecode pandas tensorflow
```

Le téléchargement des ressources NLTK (`punkt`) est inclus dans le code et se fait automatiquement. Si besoin, il peut être fait manuellement dans le shell Python :

```python
import nltk
nltk.download('punkt')
exit()
```

**2. Lancer le chatbot avec son interface graphique :**

```bash
python chatbot.py
```

## Technologies utilisées

- [Python](https://www.python.org/) (≥ 3.9)
- [TensorFlow / Keras](https://www.tensorflow.org/) : réseau de neurones pour la reconnaissance d'intentions
- [NLTK](https://www.nltk.org/) et [Unidecode](https://pypi.org/project/Unidecode/) : prétraitement du texte
- [NumPy](https://numpy.org/) et [pandas](https://pandas.pydata.org/) : manipulation des données
- [SQLite3](https://www.sqlite.org/) : base de données
- Tkinter : interface graphique

