#%%
import numpy as np
from numpy.random import permutation
from scipy.spatial.distance import cdist
from pipe import pipe
import logging as log

log.basicConfig(level=log.WARNING,format='%(relativeCreated)6d %(threadName)s %(funcName)s %(message)s') 
logger = log.getLogger('Node')
logger.setLevel(log.WARNING)

class Node:
    """A node in the classification tree, this is the heart of the probabilistic cover tree
    """
    
    modes=['find_cover','idle','split_loop']
    """modes of operation
    find_cover: find the cover points
    idle: waiting between cover found and split loop
    split_loop: split the data into subsets
    """
    
    def set_mode(self,mode):
        assert mode in Node.modes
        self.mode=mode
    def get_mode(self):
        return self.mode
    
    def __init__(self,callback,epsilon=1.,p=0.01):
        """create a node

        Args:
            epsilon (float, optional): The max distance beetween a centroid and any point in the cover. Defaults to 1.
            p (float, optional): The probability of a point further from epsilon from any point in the cover. Defaults to 0.01.
        """
        
        self.callback=callback
        self.epsilon=epsilon
        self.p=p
        self.cover=None
        self.set_mode('find_cover')
        self.accum_data=[]
        self.counters=None
        
    def master_loop(self,X):
        try:
            mode=self.get_mode()
            if mode=='find_cover':
                self.find_cover_loop(X)
                return None
        
            if mode=='split_loop':
                subsets=self.splits_loop(X)
                return subsets
            
            # else
            return None
        except Exception as exc:
            logger.exception(f'exception {exc}')
        
    def find_cover_loop(self,X, first=None):
        """This method is executed in a loop executor. It finds the cover points"""
        logger.info(f'find_cover_loop={X}')
        if X.shape[0]>0:
            self.accum_data.append(X)
            cover=self.cover
            if cover is None:
                if not first is None:
                    cover=first  # set first cover point
                else:
                    cover=X[0:1,:]  # use first example as first cover point
            
            logger.info(f'find_cover pre-iteration, cover.shape={cover.shape} X.shape={X.shape}')
            self.cover,self.found=self._find_cover_iter(cover,X)
            logger.info(f'find_cover_iter post-iteration, cover.shape={self.cover.shape}, found={self.found}')

            if not self.found:
                logger.info(f'find_cover found cover of size {cover.shape}')
                self.set_mode('idle')
                self.callback(self)
            return False
    
    def _find_cover_iter(self,cover:np.array,X:np.array):
        """Find the next cover points in X and add them to cover"""
        m=X.shape[0]
        found=False
        for i in range(m):
            x=np.array([X[i,:],])  # can make more efficient by checking several at once and keeping 
                          # track of the location of the last find.
            _,dist=self._find_dists(x,cover)
            if np.min(dist)>self.epsilon:
                logger.info(f'## In find_cover_iter adding to cover iteration {i} min dist = {np.min(dist)} cover.shape={cover.shape}')
                cover=np.concatenate([cover,x],axis=0)
                found=True
        logger.info('find_cover_iter about to return')
        return cover,found

    def splits_loop(self,X):
        """This method is executed in a loop executor. It splits the cover points into subsets
        X: input data block
        """
        try:
            #assert type(self.accum_data)==np.array
            if self.accum_data.shape[0]>0:
                X=np.concatenate([X,self.accum_data],axis=0)
                self.accum_data=np.zeros([0,0])
            if X.shape[0]==0:
                return False
            
            logger.info(f'splits input X shape {X.shape}')
            subsets=self._split_array(X,self.cover)
            #assert len(subsets)==len(self.sinks), f'len(subsets={len(subsets)}, len(self.sinks)={len(self.sinks)}'
            if self.counters is None:
                self.counters=np.zeros(len(subsets))
                
            for i in range(len(subsets)):
                self.counters[i]+=subsets[i].shape[0]   #count the total number of examples in each sink
            logger.warning(f'counters={self.counters}')
            self.subsets=subsets
            return subsets
  
        except Exception as exc:
            logger.exception(f'callback  exception {exc}')
            return False
            
    def _split_array(self,X:np.array,cover:np.array) -> list:
        """ Partition rows in X according to the cclosest row in cover"""

        index,_ = self._find_dists(X,cover)

        subsets=[]
        for i in range(cover.shape[0]):
            s=X[np.nonzero(index==i),:]
            subsets.append(s[0,:,:])
        return subsets

    def refine_cover(self,iterations=5)->np.array:
        """Performs KNN refinement of cover iterations times 

        Args:
            iterations (int, optional): number of iterations. Defaults to 5.

        Returns:
            np.array: refined cover
        """
    
        logger.info(f'refine cover {iterations} iterations')
        assert type(self.accum_data) == list
        data=np.concatenate(tuple(self.accum_data),axis=0)
        self.accum_data=data
        cover=self.cover
        logger.info(f'refine cover {iterations} iterations, data.shape={data.shape}, cover.shape={cover.shape}')

        for i in range(iterations):
            logger.info(f'refine cover iteration {i}')
            subsets=self._split_array(data,cover)   #split
            logger.info(f'refine cover iteration {i} {len(subsets)} subsets')

            
            ncover=[]
            MS_l=[]

            for s in subsets:           #refine
                _mean=np.mean(s,axis=0)
                MS=np.sum((s-_mean)**2)
                ncover.append(_mean)
                MS_l.append(MS)
            ncover=np.stack(ncover)
            logger.info(f'refine_cover RMS={np.sqrt(np.mean(MS_l))}')
            cover=ncover
        self.cover=cover
        return cover
    
    def _find_dists(self,X,rep):
        """Find the distance between each row in X and the closest row in rep"""
        C=cdist(X,rep)
        index=np.argmin(C,axis=1)
        dist=np.min(C,axis=1)
        return index,dist

    def calc_stats(subsets:list, cover:np.array)->dict:
        """Calculate statistics about a partitioned defined by subsets and cover"""
        assert len(subsets)==cover.shape[0]
        
        stats={}
        stats['cover_size']=cover.shape[0]
        sizes=np.array([a.shape[0] for a in subsets])
        fracs=sizes/np.sum(sizes)
        stats['subset sizes']=sizes
        stats['subset fractions']=fracs
        stats['entropy ratio']=sum(fracs*np.log(1/fracs))/np.log(fracs.shape[0])
        errors=[sum(np.min(cdist(subsets[i],cover),axis=1)) for i in range(len(subsets))]
        mean_errs=errors/sizes
        stats['mean errors']=mean_errs
        stats['errors']=errors
        
        return stats
if __name__=='__main__':

    try:
        def callback(node):
            node.accum_data=[data[i:i+1000,:] for i in range(0,data.shape[0],1000)]
            logger.info(f'callback, node mode={node.get_mode()}')
            node.refine_cover()
            node.set_mode('split_loop') 
            
        node=Node(callback,epsilon=1)
        node.set_mode('find_cover')
        

        filename='../../data/square.npy'
        with open(filename,'rb') as in_handle:
            data=np.load(in_handle,allow_pickle=True)
            logger.warning(f'data.shape={data.shape}')
            

        for i in range(0,data.shape[0],1000):
            X=data[i:i+1000,:]
            subsets=node.master_loop(X)
            if subsets is None:
                logger.info(f'find_cover {i}: subsets=None')
            else:
                logger.warning(f'splitting {i}: subsets={len(subsets)}') 
                
        cover=np.array([[ 0.5460406 , -0.54267738],\
                        [-0.50103154,-0.5313396 ],\
                        [ 0.11732198, 0.18823411],\
                        [-0.56734351,  0.53111045],\
                        [ 0.6318644 ,  0.59173735]]) 
        
        assert np.sum((node.cover-cover)**2)<1e-6
        logger.warning(f'cover is correct=\n{node.cover}')  
        
        stats=Node.calc_stats(subsets,node.cover)
        logger.warning(f'stats={stats}')
        
        
    except Exception as exc:
        log.exception(f'exception {exc}') 
        


    
    

        
    
    

