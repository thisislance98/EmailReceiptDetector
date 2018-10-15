
# coding: utf-8

# In[1]:


from nltk import word_tokenize
from collections import defaultdict
import pandas as pd
from collections import Counter
from sklearn.model_selection import train_test_split
import io
import numpy as np
import nltk


# In[2]:


df = pd.read_csv('o365Data.csv', dtype=object)


# In[3]:


all_subjects = df['EmailSubject'].tolist()


# In[4]:


receipt_subjects = [s.lower() for s in all_subjects if isinstance(s,str)]


# In[5]:


# import mailbox
# mbox = mailbox.mbox('emails.mbox')
# non_receipt_subjects = []
# for message in mbox:
#     payload = message.get_payload(decode=False)
#     non_receipt_subjects.append(message['Subject'])
# #     if isinstance(payload,list):
# #         non_receipt_emails.append(payload[0])
# #     else:
# #         non_receipt_emails.append(payload) 


# In[6]:


gmail_df = pd.read_csv('gmail_training_data.csv', dtype=object)
gmail_df['Subjects'].replace('', np.nan, inplace=True)
gmail_df.dropna(subset=['Subjects'], inplace=True)

x_train = gmail_df['Subjects'].tolist()
y_train = gmail_df['Is_Receipt'].tolist()
y_train = np.array(y_train).astype(np.float).tolist()

x_train = x_train + receipt_subjects
y_train = y_train + np.ones(len(receipt_subjects)).astype(np.float).tolist()

test_df = pd.read_csv('test_data.csv', dtype=object)
test_df['Subjects'].replace('', np.nan, inplace=True)
test_df.dropna(subset=['Subjects'], inplace=True)

x_test = test_df['Subjects'].str.lower().tolist()
y_test = test_df['Is_Receipt'].tolist()
y_test = np.array(y_test).astype(np.float).tolist()




# In[7]:


# creates the test set

# import csv

# subs = [s for s in non_receipt_subjects if isinstance(s,str)]
# receipt_words = ['invoice','receipt','amazon','paypal','payment','confirmation','trip','booking','order','reservation','confirmed','itinerary','statement','folio','bill']

# receipt_subs = [s.lower() for s in subs if any(word.lower() in s.lower() for word in receipt_words)]
# non_receipt_subs = [s.lower() for s in subs if not any(word.lower() in s.lower() for word in receipt_words)]

# all_subs = receipt_subs + non_receipt_subs
    
# with open("test_set.csv",'w') as resultFile:
#     wr = csv.writer(resultFile, dialect='excel')
#     for row in receipt_subs:
#         wr.writerows([[row,1]])
#     for row in non_receipt_subs:
#         wr.writerows([[row,0]])


# In[8]:


def clean_gmail_subjects(subs): 
    subs = [s for s in subs if isinstance(s,str)]
    
#    remove_words = ['invoice','utf','utf-8','receipt','amazon','paypal','payment','confirmation','hughes','trip','booking','lance','weston','order','reservation','confirmed','itinerary','statement','folio','bill']
    remove_words = ['utf','utf-8']

    return[s.lower() for s in subs if not any(word.lower() in s.lower() for word in remove_words)]


# In[9]:


# non_receipt_subjects = clean_gmail_subjects(non_receipt_subjects)


# In[10]:



# import random

# # takes in two lists. the negative list and positive and returns a randomized list off all 
# # data along with 1 or 0 labels 
# def get_randomized_data_with_labels(zeros_list,ones_list):
#     labels = np.zeros(len(zeros_list)).tolist() + np.ones(len(ones_list)).tolist()
    
#     all_data = zeros_list + ones_list
#     combined = list(zip(all_data, labels))
#     random.shuffle(combined)

#     all_data[:], labels[:] = zip(*combined)
#     return all_data,labels


# In[11]:


# subjects, labels = get_randomized_data_with_labels(non_receipt_subjects,receipt_subjects)


# In[12]:


from sklearn.linear_model import SGDClassifier
from sklearn.pipeline import Pipeline
from sklearn.naive_bayes import MultinomialNB
from sklearn.feature_extraction.text import TfidfTransformer
from sklearn.feature_extraction.text import CountVectorizer
from sklearn.model_selection import train_test_split

predicted = []

def classify(x_train,y_train,x_test,y_test):
    global predicted
#     x_train, x_test, y_train, y_test = train_test_split(data, labels, test_size=0.33, random_state=42)
    vectorizer = CountVectorizer()
#     clf = MultinomialNB()
    clf = SGDClassifier(loss='hinge', penalty='l1', alpha=1e-4, random_state=42, max_iter=7, tol=None)
    pipe = Pipeline([('vect', vectorizer),
                        ('tfidf', TfidfTransformer()),
                        ('clf', clf)
                        ])
                        
    pipe.fit(x_train, y_train)  
    predicted = pipe.predict(x_test)
    
    return np.mean(predicted == y_test), clf, vectorizer,pipe


# In[13]:



accuracy, clf, vectorizer,pipe = classify(x_train,y_train,x_test,y_test)
# print(accuracy)


# In[14]:


from sklearn import metrics
# print(metrics.classification_report(y_test, predicted))


# In[15]:


# z = [x_test[i] for i in range(len(x_test)) if y_test[i] == 0 and predicted[i] == 1]
# z


# In[20]:


# body = "your card was declined"

# pipe.predict([body])


# In[17]:


def is_receipt(subject):
    return pipe.predict([subject])[0] == 1


# In[32]:


def get_top_features_names(n=20):
    feature_names = vectorizer.get_feature_names()
    coefs_with_fns = sorted(zip(clf.coef_[0], feature_names))
    top = [x[1] for x in coefs_with_fns[:-(n + 1):-1]]
    return top
 


# In[18]:


def show_most_informative_features(vectorizer, clf, n=20):
    feature_names = vectorizer.get_feature_names()
    coefs_with_fns = sorted(zip(clf.coef_[0], feature_names))
    top = zip(coefs_with_fns[:n], coefs_with_fns[:-(n + 1):-1])
    for (coef_1, fn_1), (coef_2, fn_2) in top:
        print ("\t%.4f\t%-15s\t\t%.4f\t%-15s" % (coef_1, fn_1, coef_2, fn_2))


# In[33]:


# show_most_informative_features(vectorizer,clf,50)

