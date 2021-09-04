import os


for filename in os.listdir('./'):
    if filename.endswith(".txt") : 
        os.rename(filename, filename.replace('.txt','_US.csv'))