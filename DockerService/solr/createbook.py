import random
with open("book.txt", 'a+') as f:
    f.write("id,cat,name,price,inStock,author,series_t,sequence_i,genre_s\n")
    for i in range(11111110):
        n = random.randint(1,11111111111)
        f.write('{},book,A Storm of Swords,7.99,true,George R.R. Martin,"A Song of Ice and Fire",3,fantasy\n'.format(n))
