# -*- coding: utf-8 -*-
"""NLP_Ass4.ipynb

Automatically generated by Colaboratory.

Original file is located at
    https://colab.research.google.com/drive/1Bh6CYntXI_GmgPF699aIgnIGLTiu5qCN

Name:    Aleezeh Usman

Roll #:  18I-0529

Email:   i180529@nu.edu.pk

# **Getting the Data and formatting it into Unigram and Error Model Tables**
"""

#libraries needed to read the text - we have used google drive for file reading
import csv
from google.colab import drive
drive.mount('/content/drive', force_remount=False)
training_set = list()

from collections import Counter
import re
#read file and convert it into usable list which will be used to make the training set
#basic data set that will be used for unigram model
with open('/content/drive/My Drive/Classroom/Natural Language Processing (Spring 2021)/Notebooks/data.txt', 'r') as f:
    text = f.read()

    data_set = Counter(re.findall(r'\w+', text.lower()))
f.close()

#misspellings data set that will be used for error matrices
with open('/content/drive/My Drive/Classroom/Natural Language Processing (Spring 2021)/Notebooks/misspellings.txt', 'r') as f:
    reader = csv.reader(f)
    errors = list(reader)
f.close()

print(len(data_set))
print(len(errors))

#convert the raw data from misspellings file to usable formatted dictionary
misspellings = dict()

for each in errors:
  tempstore = ""
  templist =  list()
  for letter in each[1]:
    if letter != " " and letter != "\t":
      tempstore += letter 
    else:
      if tempstore != "":
        templist.append(tempstore)
      tempstore = ""
  if tempstore != "":
    templist.append(tempstore)
  misspellings[each[0]] = templist.copy()

values = data_set.values()
totalwords = sum(values)
#convert count in data set into a probability of occurence of the word in the data set 
for key in data_set:
  data_set[key] = data_set[key]/totalwords

"""checkcount = 0
for key in data_set:
  print(key, end = " -> ")
  print(data_set[key])
  checkcount += data_set[key]

print("TOTAL: ")
print(checkcount)

values = data_set.values()
totalwords = sum(values)
print(totalwords)

print(max(values))"""

#list that is only to help us properly format error model tables
alphabets = ['#','a','b','c','d','e','f','g','h','i','j','k','l','m','n','o','p','q','r','s','t','u','v','w','x','y','z','$']
#error model tables
#each error model table will be a 2D dictionary so each alphabet has a list of all alphabets count so error probabilities can be calculated
insert_table = dict()                                                          
delete_table = dict()
transpose_table = dict()
substitute_table = dict()
#Bigram model matrix - 2D dict
#row depicts prev word, column depicts next word
bigram_matrix = dict()
#Unigram Model - simple dictionary storing count of each character
unigram = dict()

"""# **FUNCTIONS USED FOR IMPLEMENTATION**
- insert , delete, substitute, transpose most important functions used to build error tables and find candidates from data set given a misspelled word
- Build Tables Function that will populate and store count for each operation in each table
- Build character level Bigram and Unigram used to get probabilities later
- Get Best Options function which will be used in case no candidates one edit distance away available so will give naive best option found
- Generate Candidates function to get the best candidates given a misspelled word and their probabilities too
- get P(x|w) function which will calculate the probability of the misspelled word x occuring when w was intended
"""

def printErrorTable(table, alphabets):
  print("   ", end = "")
  for alph in alphabets:
    print (alph, end = " ")
  print()
  for key in table:
    print(key, end = ": ")
    for key2 in table[key]:
      print(table[key][key2], end = " ")
    print()

def BuildBigram(bigram, alphabets, data_set):
  #initialize Bigram Matrix with zeroes at first
  for letter in alphabets:
    tempdict = dict()                                                            #each dictionary key will be storing another dictionary to make 2D dict so we can access each alphabet through each alphabet
  
    for letter2 in alphabets:
      tempdict[letter2] = 0                                                      #set all counts to zero in the table at first
    bigram[letter] = tempdict

  #count consecutive letter occurences in each word of the data set
  for key in data_set:
    i = 0
    while i < len(key):
      if i == 0:
        bigram['#'][key[i]] += 1
      else:
        bigram[key[i-1]][key[i]] += 1
      i += 1

def BuildUnigram(unigram, alphabets, data_set):
  for letter in alphabets:
    unigram[letter] = 0

  for key in data_set:
    for letter in key:
      unigram[letter] += 1
      
  unigram['#'] = len(data_set)

#function to build all the error tables using misspellings dict and alphabets list
def BuildTables(ins_tab, del_tab, sub_tab, tran_tab, misspellings, alphabets):
  #initialize the table at first
  for letter in alphabets:
    tempdict1 = dict()                                                          #since everything in python is by reference to make sure that we are not accessing the same memory
    tempdict2 = dict()
    tempdict3 = dict()
    tempdict4 = dict()
  
    for letter2 in alphabets:
      tempdict1[letter2] = 0                                                    #set all counts to zero in the table at first
      tempdict2[letter2] = 0
      tempdict3[letter2] = 0
      tempdict4[letter2] = 0
    insert_table[letter] = tempdict1
    delete_table[letter] = tempdict2
    transpose_table[letter] = tempdict3
    substitute_table[letter] = tempdict4

  #set values in the table using information about the misspellings
  for key in misspellings:
    for each in misspellings[key]:                                              #for each misspelling corresponsing to an actual word test it for all operations (insert, delete, substitute, transpose)
      letters = insert_check(key, each)                                         #then increment count in the correct table
      if letters[0] != False:
        #print('INSERT TABLE ENTRY: ', end = "")
        #print(letters)
        ins_tab[letters[0]][letters[1]] += 1
      letters = delete_check(key, each)
      if letters[0] != False:
        #print('DELETE TABLE ENTRY: ', end = "")
        #print(letters)
        del_tab[letters[0]][letters[1]] += 1
      letters = substitute_check(key, each)
      if letters[0] != False:
        #print('SUBSTITUTE TABLE ENTRY: ', end = "")
        #print(letters)
        sub_tab[letters[0]][letters[1]] += 1
      letters = transpose_check(key, each)
      if letters[0] != False:
        #print('TRANSPOSE TABLE ENTRY: ', end = "")
        #print(letters)
        tran_tab[letters[0]][letters[1]] += 1

def insert_check(actual,misspell):
  storebefore = list()                                                          # to store the word before the inserted word

  if (len(misspell) != len(actual)+1):                                          #if length of misspelling is less than or equal to actual then it is not insertion so no point running loop
    storebefore.append(False)
    return storebefore
  
  i = 0
  j = 0
  count = 0                                                                     #keep count of similar words, for insertion should be equal to length of actual word
  incorrectcount = 0
  while i < len(actual) and incorrectcount <= 1:                                #stop loop if more than 1 edit distance at the moment
    if actual[i] == misspell[j]:                                                #if similarity found keep count
      count += 1
      if ( i == len(actual)-1) and (storebefore == []) and (len(misspell) > len(actual)) and ( count == len(actual)):   
        j += 1                                                                  #if entire word was same and end has come but actual word has not ended that means insertion is at end
        storebefore.append(misspell[j-1])
        storebefore.append(misspell[j])
    elif (incorrectcount < 1 and actual[i] == misspell[j+1]):                   #if current word does not match but next does then that means this is where insertion has occured but if already an incorrect word has occurred and according to assignment document only 1 edit distance must exist so keep check
      incorrectcount += 1
      if i == 0:
        storebefore.append('#')                                                 #insertion is at the start of the word
        storebefore.append(misspell[j])
      else:
        storebefore.append(misspell[j-1])                                       #insertion occured somewhere in the middle of the word
        storebefore.append(misspell[j])
      i -= 1
    else:
      incorrectcount += 1
    i += 1
    j += 1

  if count != len(actual) or storebefore == [] or incorrectcount > 1:           #if nothing was found in loop or more incorrect words than 1 than not insertion
    storebefore = list()                                                        #just in case something was inserted in storebefore
    storebefore.append(False)

  return storebefore

def delete_check(actual,misspell):
  storebefore = list()                                                          # to store the word before the inserted word

  if (len(misspell) != len(actual)-1):                                          #if length of misspelling is longer than or equal to actual then it is not deletion so no point running loop
    storebefore.append(False)
    return storebefore
  
  i = 0
  j = 0
  count = 0                                                                     #keep count of similar words, for deletion should be equal to 1 less than length of actual word
  incorrectcount = 0
  while j < len(misspell) and incorrectcount <= 1:                              #stop loop if more than 1 edit distance
    if actual[i] == misspell[j]:                                                #if similarity found keep count
      count += 1
      if ( j == len(actual)-2) and (storebefore == []) and (len(misspell) < len(actual)) and ( count == len(actual)-1):
        i += 1                                                                  #if entire word was same and end has come but actual word has not ended that means deletion is at end
        storebefore.append(actual[i-1])
        storebefore.append(actual[i])
    elif incorrectcount < 1 and (actual[i+1] == misspell[j]):                   #if current word does not match but next does then that means this is where deletion has occuredd
      incorrectcount += 1
      if i == 0:
        storebefore.append('#')                                                 #deletion is at the start of the word
        storebefore.append(actual[i])
      else:
        storebefore.append(actual[i-1])                                         #deletion occured somewhere in the middle of the word
        storebefore.append(actual[i])
      j -= 1
    else:
      incorrectcount += 1
    i += 1
    j += 1

  if (count != len(actual)-1) or storebefore == [] or incorrectcount > 1:       #if one word less than actual word did not exist in the misspelling than not a case of deletion
    storebefore = list()                                                        #just in case something was inserted in storebefore
    storebefore.append(False)

  return storebefore

def substitute_check(actual,misspell):
  storeletters = list()

  if(len(actual) != len(misspell)):                                             #length must be same, if not no need to check
    storeletters.append(False)
    return storeletters

  i = 0
  count = 0
  while i < len(actual):
    if actual[i] == misspell[i]:                                                #if similarity found keep count
      count += 1
    else:
      storeletters.append(actual[i])                                            #if no similarity then consider than the position for subsitution
      storeletters.append(misspell[i])
    i += 1

  if (count != len(actual)-1) or storeletters == []:                            #substitution only valid IF all letter other than 1 match in misspell and actual word
    storeletters = list()
    storeletters.append(False)

  return storeletters

def transpose_check(actual, misspell):
  storeletters = list()

  if(len(actual) != len(misspell)):                                             #if length not same no need to check
    storeletters.append(False)
    return storeletters

  i = 0
  count = 0
  while i < len(actual):
    if actual[i] == misspell[i]:                                                #count similarities
      count += 1
    else:
      if ( i != len(actual)-1):                                                 #if not similar compare the current pair of letters with the pair of letters from misspelling, if they are simply interchanged it is a transpose
        if actual[i] == misspell[i+1] and misspell[i] == actual[i+1]:
          storeletters.append(actual[i])
          storeletters.append(misspell[i])
          i+=1                                                                  #move on to the next unchecked letter
    i+=1
  
  if (count != len(actual)-2) or storeletters == []:                            #all letters save for 2 MUST be same for transpose to be valid
    storeletters = list()
    storeletters.append(False)

  return storeletters

#The probability of getting x after w using the error models/tables
def get_Pxw(operation, ins_tab, del_tab, sub_tab, tran_tab, prev,curr, bigram, unigram):
  if operation == "insert":
    count = ins_tab[prev][curr]     #number of times current letter has been inserted after given prev letter
    total = unigram[prev]           #total number of the prev letter occured in the corpus/training set

  elif operation == "delete":       
    count = del_tab[prev][curr]     #number of times curr letter has been deleted after the prev letter
    total = bigram[prev][curr]      #number of times prev curr have occured together in same seq in the corpus

  elif operation == "substitute":
    count = sub_tab[prev][curr]     #number of times current letter has replaced the given prev letter
    total = unigram[prev]           #total number of the prev letter occured in the corpus/training set

  elif operation == "transpose":
    count = tran_tab[prev][curr]    #number of times current letter and prev letter have interchanged their positions     
    total = bigram[prev][curr]      #number of times prev curr have occured together in same seq in the corpus

  probability = count/total*100
  return probability

#this will only be used in case no candidates are possible with the given data set thus we will simply look for words most similar to the current word
def get_best_options(misspell, data_set):
  toReturn = list()

  for each in data_set:
    templist = list()
    i = 0
    if len(each) < len(misspell): 
      i = len(each)
    elif len(misspell) < len(each):
      i = len(misspell)
    j = 0
    count = 0
    while j < i:
      if (each[j] == misspell[j]):
        count += 1
      j += 1 
    if count > 0 :
      templist.append(each)
      templist.append(count)
      toReturn.append(templist)
  
  toReturn.sort(key = lambda x: x[1])                                           #sort so all closest to word are at end and we can easily get the best options

  finalReturn = list()
  if len(toReturn) > 4:                                                         #only return the best 4 options
    i = len(toReturn) - 1
    while i > len(toReturn) - 6:                                        
      finalReturn.append(toReturn[i][0])
      i -= 1
  else:                                                                         #if less than 4 than return all found options
    for each in toReturn:
      finalReturn.append(each[0])

  return finalReturn

#function to generate a list of candidate words that are only one edit distance away or provide options in case no candidate words available
def Generate_Candidate_Words(misspell, data_set, insert_table, delete_table, substitute_table, transpose_table, bigram, unigram):
  toReturn = list()
  finalReturn = list()

  for each in data_set:
    yesorno = insert_check(each, misspell)                                      #check if word is one edit away
    if (yesorno[0] != False):
      templist = list()
      ProbXW = get_Pxw("insert",insert_table,delete_table,substitute_table, transpose_table, yesorno[0], yesorno[1], bigram, unigram)
      ProbW = data_set[each]
      Prob = ProbXW * ProbW                                                     #calculate probability and store
      templist.append(each)
      templist.append(Prob)
      toReturn.append(templist)

    yesorno = delete_check(each, misspell)                                      #check if word one delete away
    if (yesorno[0] != False):
      templist = list()
      ProbXW = get_Pxw("delete",insert_table,delete_table,substitute_table, transpose_table, yesorno[0], yesorno[1], bigram, unigram)
      ProbW = data_set[each]
      Prob = ProbXW * ProbW                                                     #calculate probability and store
      templist.append(each)
      templist.append(Prob)
      toReturn.append(templist)

    yesorno = substitute_check(each, misspell)                                  #check if word one substitute away
    if (yesorno[0] != False):
      templist = list()
      ProbXW = get_Pxw("substitute",insert_table,delete_table,substitute_table, transpose_table, yesorno[0], yesorno[1], bigram, unigram)
      ProbW = data_set[each]
      Prob = ProbXW * ProbW                                                     #calculate probability and store
      templist.append(each)
      templist.append(Prob)
      toReturn.append(templist)

    yesorno = transpose_check(each, misspell)                                   #check if word one transposition away
    if (yesorno[0] != False):
      templist = list()
      ProbXW = get_Pxw("transpose",insert_table,delete_table,substitute_table, transpose_table, yesorno[0], yesorno[1], bigram, unigram)
      ProbW = data_set[each]
      Prob = ProbXW * ProbW                                                     #calculate probability and store
      templist.append(each)
      templist.append(Prob)
      toReturn.append(templist)

  if toReturn == []:                                                            #in case there are no candidate words
    finalReturn.append("do not process")                                        #in case there were no candidate words let program know bayes theorem and calculation can not be applied simply chose best
  else:
    finalReturn.append("process")                                               #in case candidate words where generated process further for best candidate based on error probabilities!
  
  finalReturn.append(toReturn)
  return finalReturn

"""# **Selection Model Function which is basically combining all the functions and finding the final most optimal/probable answer**"""

def Selection_Model(misspell, data_set, insert_table, delete_table, substitute_table, transpose_table, bigram, unigram):
  if misspell not in data_set:
    cand = Generate_Candidate_Words(misspell, data_set, insert_table, delete_table, substitute_table, transpose_table, bigram, unigram)
    if cand[0] == 'do not process':                   #in case no candidate words found that are one edit distance away
      print("NO CANDIDATE WORDS COULD BE GENERATED FOR THE GIVEN MISSPELLED WORD\n<<<< CLOSEST NAIVE OPTION BEING DISPLAYED>>>>")
      options = get_best_options(misspell, data_set)  #find best possible options from the data set
      print(options)
      print("BEST OPTION: ", end = "" )               #choose closest option
      print(options[0])
    if cand[0] == 'process':
      cand[1].sort(key = lambda x: x[1])              #sort list of candidates from lowest to highest probability
      print("CANDIDATE WORDS GENERATED: ", end = "")
      print(cand[1])
      print("BEST CANDIDATE: ", end = "")
      finalcandidate = cand[1][len(cand[1])-1][0]     #choose candidate with highest probability
      print(finalcandidate)
  else:
    print("<<<< WORD IS CORRECTLY SPELLED >>>>")

"""## **MAIN IMPLEMENTATION**"""

#Build and print tables
BuildTables(insert_table,delete_table, substitute_table, transpose_table, misspellings, alphabets)
BuildBigram(bigram_matrix, alphabets, data_set)
BuildUnigram(unigram, alphabets, data_set)

#print("<<<<<INSERT TABLE>>>>>")
#printErrorTable(insert_table, alphabets)
#print()
#print("<<<<<DELETE TABLE>>>>>")
#printErrorTable(delete_table, alphabets)
#print()
#print("<<<<<SUBSTITUTE TABLE>>>>>")
#printErrorTable(substitute_table, alphabets)
#print()
#print("<<<<<TRANSPOSE TABLE>>>>>")
#printErrorTable(transpose_table, alphabets)
#print()

#printErrorTable(bigram_matrix, alphabets)
#print(unigram)

#run main selection function on different words for testing (this will do all the work for us)
Selection_Model('kaa', data_set, insert_table, delete_table, substitute_table, transpose_table, bigram_matrix, unigram)
print()
Selection_Model('zzx', data_set, insert_table, delete_table, substitute_table, transpose_table, bigram_matrix, unigram)
print()
Selection_Model('ksd', data_set, insert_table, delete_table, substitute_table, transpose_table, bigram_matrix, unigram)
print()
Selection_Model('nf', data_set, insert_table, delete_table, substitute_table, transpose_table, bigram_matrix, unigram)
print()
Selection_Model('xxxxxxxxxxxxxxx', data_set, insert_table, delete_table, substitute_table, transpose_table, bigram_matrix, unigram)
print()