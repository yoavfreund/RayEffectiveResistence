import numpy as np
from numpy.random import permutation
from pipe import pipe
from NodeWrapper import NodeWrapper
from pipe import pipe
import Node as nd
import logging as log
""" """

log.basicConfig(level=log.WARNING,filename='tree.log',format='%(relativeCreated)6d %(threadName)s %(funcName)s %(message)s') 
logger = log.getLogger('tree')
logger.setLevel(log.WARNING)

class Tree:
    
    def __init__(self,infile:str,epsilon=1.,p=0.001,debug=0):
 
        from NodeWrapper import NodeWrapper
        self.executor=NodeWrapper.LoopExecutor()
    

    def main(self):
        try:
            self.pipe0=pipe(block_size=self.block_size)
            self.pid_file_loop=self.executor._start(self.file_streamer,'File Streamer')
            node=nd.Node(self.pipe0,self,epsilon=1)
            node.set_mode('find_cover')
            self.pid_node0=self.executor._start(node.master_loop,'Node Loop')
        
            from time import sleep    
            for i in range(40):
                logger.warning(f'main loop {i} node mode= {node.mode}')
                logger.warning(self.executor.futures)
                logger.warning(f'in pipe qsize={self.pipe0.qsize()}, full={self.pipe0.full()}')
                if node.get_mode()=='split_loop':
                    for j in range(len(node.sinks)):
                        p=node.sinks[j]
                        logger.warning(f'{j}: qsize={p.qsize()}, full={p.full()}') 
                sleep(2)       
        except Exception as exc:
            log.exception(f'main  exception {exc}')
        
        
if __name__=='__main__':    
    #filename='/Users/yoavfreund/datasets/NN_MNIST/MNIST/train_data.npy'
    filename='../../data/square.npy'
    yf=Tree(filename)
    yf.main()

