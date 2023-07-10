import numpy as np
from numpy.random import permutation
from pipe import pipe
from LoopExecutor import LoopExecutor
from pipe import pipe
import Node as nd
import logging as log
""" """

class Tree:
    
    def __init__(self,infile:str,epsilon=1.,p=0.001,debug=0):
        self.block_size=int(1/p)
        self.debug=debug
        self.infile=infile
        self.in_handle=open(infile,'rb')
        
        self.epsilon=epsilon
        log.basicConfig(level=log.DEBUG, format='%(relativeCreated)6d %(threadName)s %(funcName)s %(message)s')
        from LoopExecutor import LoopExecutor
        self.executor=LoopExecutor()
    

    def main(self):
        """This is the function that implements the control of the tree.
        
        It starts with a file-streamer a pipe (pipe0)  and an initial node.
        
        Each node starts in a "find cover loop" mode. in which it reads from its input pipe and 
        adds elements to the cover if theey are more than epsilon away from the current cover. This stage ends
        when for a wh0le block there is no added example.
        
        Once this happens the loop is stopped, a callback is initiated to tree, and the following steps
        are taken:
           1. the cover is refined using a few iterations of K-means (this is mostly to make the
              probabilities of the different regions more similar.)
           2. A child pipe and node is created for each cover point.
           3. The (parent) node is put in a split_loop mode and the split loop is started to
              partition first the data accumulated in the node and then data arriving at the
              input queue.
        
        nodes and pipes are named using the prefix N and P, then a sequence of comma separated numbers.
        the semantics of which is P0 = pipe at the root. P0,0 == first pipe emanating from node 0.
        Pi,j,k,l  l'th pipe emanating from node Ni,j,k
        """
        try:
            self.pipe0=pipe(block_size=self.block_size)
            self.pid_file_loop=self.executor._start(self.file_streamer,'File Streamer')
            node=nd.Node(self.pipe0,self,epsilon=2900)
            self.pid_node0=self.executor._start(node.find_cover_loop,'Cover Loop')
        
            from time import sleep    
            for i in range(4):
                log.debug(f'main loop {i} node mode= {node.mode}')
                log.debug(self.executor.futures)
                
                for j in range(len(node.sinks)):
                    p=node.sinks[j]
                    log.warning(f'{j}: qsize={p.qsize()}, full={p.full()}') 
                                
                sleep(1)
        except Exception as exc:
            log.exception(f'main  exception {exc}')
    
    def cover_found_callback(self,node:nd):
        try:
            log.warning(f'cover_found_callback {node.cover.shape}')
            node.refine_cover ()
            log.warning(f'cover_found_callback refined {node.cover.shape}')
            self.create_children(node)
            self.pid_split_loop=self.executor._start(node.splits_loop,'split loop')
            node.mode='splitting'

    
        except Exception as exc:
            log.exception(f'callback  exception {exc}')

    def create_children(self,nd:nd):
   
        nd.number_of_children=nd.cover.shape[0]
        log.warning(f'')
        nd.sinks=[]
        #nd.child_nodes=[]
        #self.pid_node_loops=[]
        for nd.i in range(nd.number_of_children):
            nd.sinks.append(pipe(block_size=self.block_size)) 
            # nd.child_nodes.append(nd.Node(nd.outpipe[-1],self,debug=4,epsilon=2000))
            # self.pid_nodeloops.append(self.executor._start(nd.sinks[-1].find_cover_loop,f'Cover Loop {nd.i}')
        #self.pid_split_loop=self.executor._start(nd.splits_loop,f'Cover Loop {nd.i}')
        
 
    def file_streamer(self):
        log.info('file_streamer')
        data=np.load(self.in_handle)
        self.pipe0.put(data)
        return False
    
    #executor.shutdown(wait=False,cancel_futures=True)   
    
    #node=Node(pipe0,debug=True,epsilon=2800)        

if __name__=='__main__':    
    yf=Tree('/Users/yoavfreund/datasets/NN_MNIST/MNIST/train_data.npy')
    yf.main()

