class pipe:
    def __init__(self,block_size=100,debug=False):
        self.queue=queue.Queue()
        self.block_size=block_size
        self.block=np.ones([0,0])
        self.width=0
        self.debug=debug
        
    def put(self,data):
        """chop incoming data into blocks of equal size and send through queue"""
        assert type(data)==np.ndarray
        _,w=data.shape
        if self.width==0:
            self.width=w
        else:
            assert self.width==w
        
        if self.block.shape==(0,0):
            self.block=np.ones([0,w])
            
        while data.shape[0]>0:
            if self.debug:
                print('data shape=',data.shape[0],'block shape=',self.block.shape[0])
            # check if remaining data fits into buffer
            space=self.block_size-self.block.shape[0]
            if space<=data.shape[0]:
                if self.debug:
                    print('<= ',space,self.block.shape,data.shape)
                self.block=np.concatenate([self.block,data[:space,:]],axis=0)
                data=data[space:,:]
            else:
                if self.debug:
                    print('> ',space,self.block.shape,data.shape)
                self.block=np.concatenate([self.block,data],axis=0)
                data=np.ones([0,w])

            if self.block.shape[0] ==self.block_size:
                self.queue.put(self.block)
                self.block=np.ones([0,w])
                                            
    def get(self,block=True):
        try:
            item=self.queue.get(block=block)
        except queue.Empty:
            return None
        return item
    
    

P=pipe(block_size=10,debug=True)

for i in range(10):
    item=i*np.ones([3,10])
    P.put(item)
    print('put ',i,end=' ')
    out=P.get(block=False)
    if out is None:
        print('got Nothing')
    else:
        print('got ',out.shape)
