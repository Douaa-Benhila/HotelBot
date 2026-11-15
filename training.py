
#this file will help me train my chatbot with my data
import random  #choosing random response 
import json   #import my json file 
import pickle  #savgarder des objets pour les recuperer apres 
import numpy as np 
import tensorflow as tf 
import os
import re

#import pout TAL 
import nltk
from nltk.stem.snowball import FrenchStemmer # reduce the word: work , working , workes this all the same world 

# Fixer les seeds pour reproductibilité
os.environ["PYTHONHASHSEED"] = "0"
random.seed(0)
np.random.seed(0)
tf.random.set_seed(0)


#-------chargement des données_________________________

with open('intents.json', encoding='utf-8') as f:
    intents = json.load(f)
 #load my file and read it and i put inb object which will be a dictionnary 

#---------------prétraitement des données --------------------------------
stemmer = FrenchStemmer() # reduit un mot a la racine 
def normalize_text(s: str) -> str:
    from unidecode import unidecode
    s = unidecode(s).lower()
    s = re.sub(r"[^a-z0-9€\-'/ ]+", " ", s)
    return re.sub(r"\s+", " ", s).strip()

#--------construction du vocabulaire------------------

words = [] #les mots rencontrées 
classes = [] #les tags 
documents = [] #couple phrase: tag 
ignoreLetters = ['?', '!', '.', ','] # stuff will not be taking to account 


#tokennisation + annotation (je tokenise entrée et j'associe chaque phrase a son tag)
# i will iterates in intenents 

for intent in intents['intents']:
    for pattern in intent['patterns']:
        pattern = normalize_text(pattern)
        wordList = nltk.word_tokenize(pattern) #split the list a word in tokens (words in certain length )(tal)
        words.extend(wordList)
        documents.append((wordList, intent['tag'])) #this word is attach to this category 
        if intent['tag'] not in classes:
            classes.append(intent['tag'])


words = [stemmer.stem(word) for word in words if word not in ignoreLetters]
words = sorted(set(words)) #set illiminate dupplicates 

#classes = sorted(set(classes))

# sauvgardage du vocabulaire et des classes 
pickle.dump(words, open('words.pkl', 'wb'))
pickle.dump(classes, open('classes.pkl', 'wb'))

#---------------- création des données d'entrainement--------------------------

training = []
outputEmpty = [0] * len(classes)

for document in documents:
    bag = []
    wordPatterns = document[0]
    wordPatterns = [stemmer.stem(word.lower()) for word in wordPatterns]
    for word in words:
        bag.append(1) if word in wordPatterns else bag.append(0)

    outputRow = list(outputEmpty)
    outputRow[classes.index(document[1])] = 1
    training.append(bag + outputRow)

random.shuffle(training)
training = np.array(training)

trainX = training[:, :len(words)]
trainY = training[:, len(words):]

#build the neural network 

model = tf.keras.Sequential()
model.add(tf.keras.layers.Dense(128, input_shape=(len(trainX[0]),), activation = 'relu'))
model.add(tf.keras.layers.Dropout(0.5))
model.add(tf.keras.layers.Dense(64, activation = 'relu'))
model.add(tf.keras.layers.Dropout(0.5))
model.add(tf.keras.layers.Dense(len(trainY[0]), activation='softmax'))

sgd = tf.keras.optimizers.SGD(learning_rate=0.01, momentum=0.9, nesterov=True)
model.compile(loss='categorical_crossentropy', optimizer=sgd, metrics=['accuracy'])

model.fit(trainX, trainY, epochs=200, batch_size=5, verbose=1)
model.save('chatbot_model.h5')
print('Done')




