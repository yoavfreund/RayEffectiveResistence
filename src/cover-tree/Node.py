import numpy as np
from numpy.random import permutation
from scipy.spatial.distance import cdist
from pipe import pipe
import logging as log


class Node:
    """A node in the classification tree, this is the heart of the probabilistic cover tree
    """
    def __init__(self,source:pipe,tree,epsilon=1,p=0.01):
        """create a node

        Args:
            source (iterator): generates a sequence of data sets
            epsilon (int, optional): The max distance between cover points. Defaults to 2700.
            p (float, optional): The probability of a point further from epsilon from any point in the cover. Defaults to 0.01.
        """
        self.source=source
        self.tree=tree
        self.epsilon=epsilon
        self.p=p
        self.cover=None
        self.mode='find_cover'
        self.accum_data=[]
        
    def find_cover_loop(self):
        
        X = self.source.get() 
        log.info(f'find_cover_loop={X.shape}')
        if X.shape[0]>0:
            self.accum_data.append(X)
            cover=self.cover
            if cover is None:
                cover=X[0:1,:]  # use first example as first cover point
            
            log.info(f'find_cover pre-iteration, cover.shape={cover.shape} X.shape={X.shape}')
            self.cover,self.found=self._find_cover_iter(cover,X)
            log.info(f'find_cover_iter post-iteration, cover.shape={self.cover.shape}, found={self.found}')

            if not self.found:
                log.info(f'find_cover found cover of size {cover.shape}')
                self.mode='cover_found'
                self.tree.cover_found_callback(self)
            return not self.found
    
    def _find_cover_iter(self,cover:np.array,X:np.array) -> (np.array,bool):
        """Find the next cover points in X and add them to cover"""
        m=X.shape[0]
        found=False
        for i in range(m):
            x=np.array([X[i,:],])  # can make more efficient by checking several at once and keeping 
                          # track of the location of the last find.
            _,dist=self._find_dists(x,cover)
            if np.min(dist)>self.epsilon:
                log.info(f'## In find_cover_iter adding to cover iteration {i} min dist = {np.min(dist)} cover.shape={cover.shape}')
                cover=np.concatenate([cover,x],axis=0)
                found=True
        log.info('find_cover_iter about to return')
        return cover,found


    def splits_loop(self):
        """This method is executed in a loop executor. It splits the cover points into subsets
        """
        try:
            #assert type(self.accum_data)==np.array
            if self.accum_data.shape[0]>0:
                X=self.accum_data
                self.accum_data=np.zeros([0,0])
            else:
                X = self.source.get() 
            if X.shape[0]==0:
                return False
            log.info(f'splits input X shape {X.shape}')
            subsets=self.split_array(X,self.cover)
            assert len(subsets)==len(self.sinks), f'len(subsets={len(subsets)}, len(self.sinks)={len(self.sinks)}'
            for i in range(len(subsets)):
                self.sinks[i].put(subsets[i]) 
        except Exception as exc:
            log.exception(f'callback  exception {exc}')
        return False
            
    def split_array(self,X:np.array,cover:np.array) -> list:
        """ Partition rows in X according to the cclosest row in cover"""

        index,dist = self._find_dists(X,cover)

        subset=[]
        for i in range(cover.shape[0]):
            s=X[np.nonzero(index==i),:]
            subset.append(s[0,:,:])
        return subset

    def refine_cover(self,iterations=5)->np.array:
        """Performs KNN refinement of cover iterations times 

        Args:
            iterations (int, optional): number of iterations. Defaults to 5.

        Returns:
            np.array: refined cover
        """
    
        log.info(f'refine cover {iterations} iterations')
        assert type(self.accum_data) == list
        data=np.concatenate(tuple(self.accum_data),axis=0)
        self.accum_data=data
        cover=self.cover
        log.info(f'refine cover {iterations} iterations, data.shape={data.shape}, cover.shape={cover.shape}')

        for i in range(iterations):
            log.info(f'refine cover iteration {i}')
            subset=self.split_array(data,cover)   #split
            log.info(f'refine cover iteration {i} {len(subset)} subsets')

            
            ncover=[]
            MS_l=[]

            for s in subset:           #refine
                _mean=np.mean(s,axis=0)
                MS=np.sum((s-_mean)**2)
                ncover.append(_mean)
                MS_l.append(MS)
            ncover=np.stack(ncover)
            log.info(f'refine_cover RMS={np.sqrt(np.mean(MS_l))}')
            cover=ncover
        self.cover=cover
        return cover
    
    def _find_dists(self,X,rep):
        """Find the distance between each row in X and the closest row in rep"""
        C=cdist(X,rep)
        index=np.argmin(C,axis=1)
        dist=np.min(C,axis=1)
        return index,dist

def split_entropy(subset:list)->float:
    """Compute the ratio of the entropy of the subset to the log of the size of the set

    Args:
        subset (list): list of subsets

    Returns:
        float: ratio of entropy to log of size, between 0 (worst) and 1 (best)
    """
    sizes=np.array([a.shape[0] for a in subset])
    sizes=sizes/np.sum(sizes)
    return sum(sizes*np.log(1/sizes))/np.log(sizes.shape[0])

if __name__=='__main__':

    pipe=pipe(block_size=1000)
    tree=Tree('/Users/yoavfreund/datasets/NN_MNIST/MNIST/train_data.npy')

    node=Node(pipe,tree,epsilon=2800)        

    from concurrent.futures import ThreadPoolExecutor
    executor=ThreadPoolExecutor(max_workers=2)
    stop_flag=[False]
    f=executor.submit(file_streamer)

    cover=node.find_cover()

    log.info('fron find_cover',cover.shape)
    stop_flag[0]=True
    executor.shutdown(wait=False,cancel_futures=True)

    
    log.info('done executor')

