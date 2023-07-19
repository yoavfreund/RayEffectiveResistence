import queue
import numpy as np
import logging as log

logger = log.getLogger('pipe')
logger.setLevel(log.WARNING)

class pipe:
    """A wrapper around queue to allow for sending data in blocks of equal size"""
    def __init__(self,block_size=100,max_queue=10,debug=False):
        """create a pipe
        """
        self.queue=queue.Queue(maxsize=max_queue) #block put when more than 10 items in queue
        self.block_size=block_size
        self.block=np.ones([0,0])
        self.width=0
        self.debug=debug
        
    def put(self,data):
        """chop incoming data into blocks of equal size and send through queue
        """
        assert type(data)==np.ndarray
        _,w=data.shape
        if self.width==0:
            self.width=w
        else:
            assert self.width==w
        
        if self.block.shape==(0,0):
            self.block=np.ones([0,w])
            
        while data.shape[0]>0:
            logger.info(f'data shape={data.shape[0]}, block shape={self.block.shape[0]}')
            # check if remaining data fits into buffer
            space=self.block_size-self.block.shape[0]
            if space<=data.shape[0]:
                logger.debug(f'more data than space: block={self.block.shape} data={data.shape}')
                self.block=np.concatenate([self.block,data[:space,:]],axis=0)
                data=data[space:,:]
            else:
                logger.debug(f'more space than data: block={self.block.shape} data={data.shape}')

                self.block=np.concatenate([self.block,data],axis=0)
                data=np.ones([0,w])

            if self.block.shape[0] ==self.block_size:
                try:
                    self.queue.put(self.block,block=True,timeout=0.001)
                except queue.Full:
                    logger.info(f'pipe put returned queue full, block size={self.block.shape}')
                else:
                    logger.info(f'pipe put returned successfully, block size={self.block.shape}')
                    self.block=np.ones([0,w])
            #from time import sleep
            #sleep(0.1)
                                            
    def get(self):
        try:
            item=self.queue.get(block=True,timeout=0.001)
        except queue.Empty:
            logger.debug('empty queue')
            return np.zeros([0,0])
        return item
    
    def qsize(self):
        return self.queue.qsize()
    def empty(self):
        return self.queue.empty()
    def full(self):
        return self.queue.full()
    
    
if __name__=='__main__':
    P=pipe(block_size=10,debug=True)

    for i in range(10):
        item=i*np.ones([3,10])
        P.put(item)
        print('put ',i,end=' ')
        out=P.get()
        if out is None:
            print('got Nothing')
        else:
            print('got ',out.shape)
