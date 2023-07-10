import numpy as np
from numpy import *
from scipy.spatial.distance import cdist

class Node:
    def __init__(self,source,epsilon=2700,p=0.01,debug=0):
        self.source=source
        self.epsilon=epsilon
        self.p=p
        self.debug=debug
        
    def find_dists(self,X,rep):
        C=cdist(X,rep)
        index=argmin(C,axis=1)
        dist=np.min(C,axis=1)
        return index,dist

    def find_cover_iter(self,cover,X) :
        m=X.shape[0]
        found=False
        for i in range(m):
            x=np.array([X[i,:],])  # can make more efficient by checking several at once and keeping 
                          # track of the location of the last find.
            _,dist=self.find_dists(x,cover)
            if np.min(dist)>self.epsilon:
                if self.debug>5:
                    print("## In find_cover_iter",i,np.min(dist),cover.shape)
                cover=concatenate([cover,x],axis=0)
                found=True
        return cover,found

    def find_cover(self):
        found=True; j=0
        cover=None
        for X in self.source():  #need to make sure cover yilds sets of size 1/p
            if cover is None:
                cover=X[0:1,:]  # use first example as first cover

            cover,found=self.find_cover_iter(cover,X)
            if self.debug>0:
                print('### round ',j,cover.shape); j+=1
            if not found:
                break
        self.cover=cover
        return (cover)

    def split(self,X,cover):
        """ Partition rows in X according to the cclosest row in cover"""
        index,dist = self.find_dists(X,cover)

        subset=[]
        for i in range(cover.shape[0]):
            s=X[nonzero(index==i),:]
            subset.append(s[0,:,:])
        return subset

    def refine_cover(self,cover,data,iterations=5):
        for i in range(iterations):
            subset=self.split(data,cover)   #split
            ncover=[]
            MS_l=[]

            for s in subset:           #refine
                _mean=np.mean(s,axis=0)
                MS=np.sum((s-_mean)**2)
                ncover.append(_mean)
                MS_l.append(MS)
            ncover=stack(ncover)
            if self.debug>1:
                print('RMS=',sqrt(np.mean(MS_l)))
            cover=ncover
        return cover
    
def split_entropy(subset):
    sizes=array([a.shape[0] for a in subset])
    sizes=sizes/np.sum(sizes)
    return sum(sizes*log(1/sizes))/log(sizes.shape[0])
