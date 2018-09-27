
# coding: utf-8

# In[2]:


from nltk import word_tokenize
from collections import defaultdict
import pandas as pd
from collections import Counter
from sklearn.model_selection import train_test_split
import io
import numpy as np
import nltk


# In[3]:


df = pd.read_csv('o365Data.csv', dtype=object)


# In[4]:


all_subjects = df['EmailSubject'].tolist()


# In[5]:


receipt_subjects = [s.lower() for s in all_subjects if isinstance(s,str)]


# In[6]:


import mailbox


# In[7]:


mbox = mailbox.mbox('emails.mbox')


# In[8]:


non_receipt_emails = []
non_receipt_subjects = []
for message in mbox:
    payload = message.get_payload(decode=False)
    non_receipt_subjects.append(message['Subject'])
    if isinstance(payload,list):
        non_receipt_emails.append(payload[0])
    else:
        non_receipt_emails.append(payload) 


# In[9]:


def clean_gmail_subjects(subs): 
    subs = [s for s in subs if isinstance(s,str)]
    
    remove_words = ['invoice','utf','utf-8','receipt','amazon','paypal','payment','confirmation','hughes','trip','booking','lance','weston','order','reservation','confirmed','itinerary','statement','folio','bill']

    return[s.lower() for s in subs if not any(word.lower() in s.lower() for word in remove_words)]


# In[10]:


non_receipt_subjects = clean_gmail_subjects(non_receipt_subjects)


# In[11]:


import random

def get_test_data_labels(zeros_list,ones_list):
    labels = np.zeros(len(zeros_list)).tolist() + np.ones(len(ones_list)).tolist()
    
    all_data = zeros_list + ones_list
    combined = list(zip(all_data, labels))
    random.shuffle(combined)

    all_data[:], labels[:] = zip(*combined)
    return all_data,labels


# In[12]:


subjects, labels = get_test_data_labels(non_receipt_subjects,receipt_subjects)


# In[13]:


from sklearn.linear_model import SGDClassifier
from sklearn.pipeline import Pipeline
from sklearn.naive_bayes import MultinomialNB
from sklearn.feature_extraction.text import TfidfTransformer
from sklearn.feature_extraction.text import CountVectorizer
from sklearn.model_selection import train_test_split
X_test = []
y_test = []
predicted = []

def classify(data, labels):
    global X_test,y_test,predicted
    X_train, X_test, y_train, y_test = train_test_split(data, labels, test_size=0.33, random_state=42)
    vectorizer = CountVectorizer()
#     clf = MultinomialNB()
    clf = SGDClassifier(loss='hinge', penalty='l1', alpha=1e-4, random_state=42, max_iter=7, tol=None)
    pipe = Pipeline([('vect', vectorizer),
                        ('tfidf', TfidfTransformer()),
                        ('clf', clf)
                        ])
                        
    pipe.fit(X_train, y_train)  
    predicted = pipe.predict(X_test)
    
    return np.mean(predicted == y_test), clf, vectorizer,pipe


# In[19]:


accuracy, clf, vectorizer,pipe = classify(subjects,labels)
print(accuracy)


# In[15]:


from sklearn import metrics
print(metrics.classification_report(y_test, predicted))


# In[16]:


z = [X_test[i] for i in range(len(X_test)) if y_test[i] == 1 and predicted[i] == 0]
z


# In[20]:


body = "your republic parking invoice"

pipe.predict([body])


# In[21]:


def is_receipt(subject):
    return pipe.predict([subject])[0] == 1


# In[23]:


is_receipt("yes")


# In[18]:


def show_most_informative_features(vectorizer, clf, n=20):
    feature_names = vectorizer.get_feature_names()
    coefs_with_fns = sorted(zip(clf.coef_[0], feature_names))
    top = zip(coefs_with_fns[:n], coefs_with_fns[:-(n + 1):-1])
    for (coef_1, fn_1), (coef_2, fn_2) in top:
        print ("\t%.4f\t%-15s\t\t%.4f\t%-15s" % (coef_1, fn_1, coef_2, fn_2))


# In[19]:


show_most_informative_features(vectorizer,clf,1000)


# In[20]:


import eli5
eli5.show_weights(clf, top=10)

