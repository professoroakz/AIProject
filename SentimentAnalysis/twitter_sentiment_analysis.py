import pandas as pd
import nltk
from numpy import * 
import re
import nltk
from nltk.corpus import stopwords
from sklearn.feature_extraction.text import CountVectorizer
from sklearn.feature_extraction import DictVectorizer
from sklearn.ensemble import RandomForestClassifier
from sklearn import svm
import timeit
import itertools
import sys


import theano
import theano.printing as p
import theano.tensor as T
from lstm_pooled import LSTM_Pooled

#Reads and Cleans  'n' tweets from corpus so we don't need to read everything
#each time we train
def extract_features(path,n):
    print "Loading Data..."
    train = pd.read_csv("training.1600000.processed.noemoticon.csv", header=None, \
                    delimiter='","', quoting=3, engine='python')
    print "Finished Loading!!!"

    #Collect clean review for both positive and negative as well as training and test
    clean_train_reviews_neg = []
    clean_train_reviews_pos = []

    clean_test_reviews_neg = []
    clean_test_reviews_pos = []

    for i in range( n ):
            clean_train_reviews_neg.append(review_to_words(train[5][i]))
            clean_test_reviews_neg.append(review_to_words(train[5][i + n]))
            
            clean_train_reviews_pos.append(review_to_words(train[5][i + 800000 ]))            
            clean_test_reviews_pos.append(review_to_words(train[5][i + 800000 + n]))
            
            if i%10000 ==0:
                print i            


    #Write everything to csv
    pos_output = pd.DataFrame( data=clean_train_reviews_pos)
    neg_output = pd.DataFrame( data=clean_train_reviews_neg)
    
    test_pos_output = pd.DataFrame( data=clean_test_reviews_pos)
    test_neg_output = pd.DataFrame( data=clean_test_reviews_neg)
    
    pos_output.to_csv(path + "pos_tweets_train.csv",index = False)
    neg_output.to_csv(path + "neg_tweets_train.csv",index = False)

    test_pos_output.to_csv(path + "pos_tweets_test.csv",index = False)
    test_neg_output.to_csv(path + "neg_tweets_test.csv",index = False)

#Cleans up a tweet - review is from when this was for IMDB
def review_to_words( raw_review ):

    no_url = re.sub("http[s]??://.+?\\..+?[ ]?", "", raw_review)

    #Remove numerics
    letters_only = re.sub("[^a-zA-Z]", " ", no_url) 

    #to lowercase
    words = letters_only.lower().split()                             

    #remove stop words - the, of , a ....
    stops = set(stopwords.words("english"))                  

    meaningful_words = [w for w in words if not w in stops]   
    
    return( " ".join( meaningful_words )) 

#predict is a funtion object that will predict sentiment
def test_model(path,n,predict,vectorizer):
    
    print "Loading Test Data..."
    test_pos = pd.read_csv(path + "pos_tweets_test.csv", header=0, \
                    delimiter=',', quoting=3, engine='python')

    test_neg = pd.read_csv(path + "neg_tweets_test.csv", header=0, \
                    delimiter=',', quoting=3, engine='python')
           
    test  = pd.concat([test_pos.iloc[0:n],test_neg.iloc[0:n]])
    
    print "Test data finished loading !"
    print "Processing Features ... "
    
    test_data_features = vectorizer.transform(test['0'].values.tolist())
    test_data_features = test_data_features.toarray()
    i = 0
    errors = 0
    for tweet in test_data_features:
        sentiment = predict(tweet)
        if i < n:
            if sentiment != 1:
                errors =errors +1
        else:
            if sentiment != 0 :
                errors = errors+1
                
        i = i+1

    print "Percent Correct:   "+str(float((i - errors)) / i)


def sentiment_analysis(path,n,k):
    print "Loading Data"
    train_pos = pd.read_csv(path + "pos_tweets_train.csv", header=0, \
                    delimiter=',', quoting=3, engine='python')

    train_neg = pd.read_csv(path + "neg_tweets_train.csv", header=0, \
                    delimiter=',', quoting=3, engine='python')
                    
    vectorizer = CountVectorizer(analyzer = "word",   \
                             tokenizer = None,    \
                             preprocessor = None, \
                             stop_words = None,   \
                             max_features = k)
                             
    print "Finished Loading!!!"

    print "Processing Bag of Word Features"
    train  = pd.concat([train_pos.iloc[0:n],train_neg.iloc[0:n]])
    sentiment = zeros(2*n)
    sentiment[0:n]  = 1
    
    train_data_features = vectorizer.fit_transform(train['0'].values.tolist())
    train_data_features = train_data_features.toarray()
    
    print "Beginning Training"
    start = timeit.default_timer()

    forest = RandomForestClassifier(n_estimators = 50)
    forest = forest.fit( train_data_features, sentiment )
    
    stop = timeit.default_timer()

    print "Training Finished!!! Total Time:  " + str( stop - start)
    
    
    return forest,vectorizer

#Sentiment analysis with LSTM
#best so far ~.72
#needs to be run against larger corpus
def sentiment_analysis_lstm(path,n,k):
    print "Loading Data"
    train_pos = pd.read_csv(path + "pos_tweets_train.csv", header=0, \
                    delimiter=',', quoting=3, engine='python')

    train_neg = pd.read_csv(path + "neg_tweets_train.csv", header=0, \
                    delimiter=',', quoting=3, engine='python')
                    
              
    print "Finished Loading!!!"

    print "Processing One Hot Features"      

    #all words in a tweet that are not in the vocab are replaced with this
    unknown_token = "UNKNOWN_TOKEN"

    #Add these in later - maybe not important
    sentence_start_token = "SENTENCE_START"
    sentence_end_token = "SENTENCE_END"

    #Take 'n' pos and  'n' neg examples - make n small while debugging
    train  = pd.concat([train_pos.iloc[0:n],train_neg.iloc[0:n]])

    #tokenize tweets
    tokenized_sentences = [nltk.word_tokenize(sent) for sent in train['0'].values.tolist()]

    #frequency of each word in the trianing corpus
    word_freq = nltk.FreqDist(itertools.chain(*tokenized_sentences))

    #our vocab is the k most frequent words
    vocab = word_freq.most_common(k-1)
    index_to_word = [x[0] for x in vocab]
    index_to_word.append(unknown_token)
    word_to_index = dict([(w,i) for i,w in enumerate(index_to_word)])

    for i, sent in enumerate(tokenized_sentences):
        tokenized_sentences[i] = [w if w in word_to_index else unknown_token for w in sent]

    #Data is now a list of arrays of ints, each array corresponds to a tweet and entry is a word index
    X_train = asarray([[word_to_index[w] for w in sent[:-1]] for sent in tokenized_sentences])

    #1 for positve tweets and 0 for negative tweets
    sentiment = zeros(2*n)
    sentiment[0:n]  = 1

    #shuffle data to prevent biasing
    data =  random.permutation( zip(X_train,sentiment) )

    print "Setting up Model"
    #This is inefficent
    #Consider changing LSTM code to directly select the right neruon    
    E = theano.shared(eye(k))
    index = T.ivector()
    
    h_dim = 10
    model = LSTM_Pooled(k, h_dim, 1 ,0)
    
    X = E[index]
    
    y_hat = model.apply(X)
    y = T.scalar()
    cost = model.cost(X,y)

    lr = .2
    
    params = model.params
    gparams = [ T.grad(cost,par) for par in params]
    updates = [ (par , par - lr*grad) for par,grad in zip(params,gparams)  ]


    train_model = theano.function(
            inputs = [index,y],
            outputs = cost,
            updates= updates
        )
    
    predict = theano.function(
            inputs = [index],
            outputs = y_hat
        )

    predict2 = theano.function(
            inputs = [index],
            outputs = model.apply_one_hot(index)
        )

    start = timeit.default_timer()
    print predict(X_train[0])
    print timeit.default_timer() - start
    start = timeit.default_timer()
    print predict2(X_train[0])
    print timeit.default_timer() - start

    print "Beginning Training"
    start = timeit.default_timer()

    epochs = 10
    
    total_error = 0
    counts = 0
    for j in range(epochs):
        #for pair in data:
        for i in range(n):
            pair = data[i]
            if len(pair[0]) > 0:
                error = train_model(pair[0],pair[1])
                total_error = total_error +error
                counts = counts + 1.0
    
        print total_error/ counts
        counts = 0
        total_error = 0
        
    stop = timeit.default_timer()

    print "Training Finished!!! Total Time:  " + str( stop - start)



    print "Loading Test Data..."

    n_test = 1000
    test_pos = pd.read_csv(path + "pos_tweets_test.csv", header=0, \
                    delimiter=',', quoting=3, engine='python')

    test_neg = pd.read_csv(path + "neg_tweets_test.csv", header=0, \
                    delimiter=',', quoting=3, engine='python')

    test  = pd.concat([test_pos.iloc[0:n_test],test_neg.iloc[0:n_test]])

    tokenized_sentences = [nltk.word_tokenize(sent) for sent in test['0'].values.tolist()]

    for i, sent in enumerate(tokenized_sentences):
        tokenized_sentences[i] = [w if w in word_to_index else unknown_token for w in sent]

    X_test = asarray([[word_to_index[w] for w in sent[:-1]] for sent in tokenized_sentences])

    sentiment = zeros(2*n_test)
    sentiment[0:n_test]  = 1

    data =  random.permutation( zip(X_test,sentiment) )

    print "Test Data Loaded. Beginning testing..."

    i = 0
    errors = 0
    for tweet in data:
       if len(tweet[0]) > 0:
            y = tweet[1]
            sentiment = predict(tweet[0])
            sentiment = 1 if sentiment > .5 else 0
            if sentiment != y:
                errors =errors +1

            i = i+1

    print "Percent Correct:   "+str(float((i - errors)) / i)



if __name__ == '__main__':
    
    #DataFrame Structure for the trianingf file
    #0 - sentiment value
    #1 - id
    #2 - date
    #3 - NO_QUERY ?
    #4 - person who tweeted
    #5 - Actual tweet
   
    path = "/Users/zachzhang/DeepLearningTutorials/KaggleWarmUp/data/"
    n = 1000
    k = 2000
    #extract_features(path,n)
    #[model,vectorizer] = sentiment_analysis(path,n,k)
    #test_model(path,n,model.predict,vectorizer)

    sentiment_analysis_lstm(path,n,k )
