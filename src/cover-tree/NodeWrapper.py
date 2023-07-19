from concurrent.futures import ThreadPoolExecutor
import logging as log
from Node import Node
from pipe import pipe

logger = log.getLogger('NodeWrapper')
logger.setLevel(log.WARNING)
 
class LoopExecutor:
   
   def __init__(self):
      self.executor=ThreadPoolExecutor(max_workers=1)
      self.futures={}
      self.futures_counter=0
      logger.info('__init__')
      
   def start_thread(self,f,name,*args,**kwargs):
      loop_counter=[0]
      self.futures_counter+=1
      self.executor._max_workers=self.futures_counter+1
      logger.info(f'executor={self.executor.__str__()}, name={name}  max_workers={self.executor._max_workers}')
      future=self.executor.submit(f,loop_counter,*args,**kwargs)

      self.futures[self.futures_counter]={'future':future,
                                          'name':name,
                                          'loop_counter':loop_counter
                                          }

         
         
class NodeWrapper:
   def __init__(self,executor:LoopExecutor,node:Node,name:str,inpipe:pipe,epsilon=1,p=0.01):
      """This class wraps a node and runs it in a thread. It also connects the input and output pipes to the node.

      Args:
          executor (LoopExecutor): The executor that will run the node loop
          node (Node): The node that is being wrapped
          inpipe (Pipe): The input pipe
          outpipes (list): The output pipes
          
      """
      self.executroe=executor
      self.node=node
      self.name=name
      self.inpipe=inpipe
      self.outpipes=None
      
      self.block_size=int(1/p)
   
     
      self.epsilon=epsilon
        
      logger.info('__init__')

   def loop(self,loop_counter:list):
      """This is a wrapper around the node loop method. It is responsible for running it within a thread and for connections the input and output pipes.

      Args:
          loop_counter (int]): A counter that is incremented each time the loop is executed. This is used to check if the loop is still running.
      """

      while True:
         if self.node.get_mode()=='idle':
            continue
         loop_counter[0]+=1
         X=self.node.inpipe.get()
         subsets = self.node.master_loop(X)
         if not subsets is None:
            if not self.node.outpipes is None:
               assert len(self.node.outpipes)==len(subsets)
               for i in range(len(subsets)):
                  self.nodesinks[i].put(subsets[i])
         logger.info(f'NodeWrapper for {self.nodename} counter={loop_counter[0]}')
         
         #if self.nodeprintme:
         #   print_subsets(subsets)  #  prints the subsets as rows in a csv file needs to use a lock to regulate printing from different threads

   def _start(self):
      try:
         
         self.inpipenode=Node(self,epsilon=self.epsilon)
         self.node.set_mode('find_cover')
       
         logger.info(f'_start {self.name}')
         return self.futures_counter
      except Exception as exc:
         logger.exception(f'exception {exc}')
   
   def cover_found_callback(self):
        try:
            node=self.node
            assert node.get_mode()=='idle'
            logger.warning(f'cover_found_callback {node.cover.shape}')
            node.refine_cover ()
            logger.warning(f'cover_found_callback refined {node.cover.shape}')
            
            self.create_children(node)
            node.set_mode('split_loop')
    
        except Exception as exc:
            log.exception(f'callback  exception {exc}')

   def create_children(self):
   
      nd=self.node
      nd.number_of_children=nd.cover.shape[0]
      nd.outpipes=[]
      #nd.child_nodes=[]
      #self.pid_node_loops=[]
      for nd.i in range(nd.number_of_children):
         nd.outpipes.append(pipe(block_size=self.block_size)) 
         logger.warning(f'create_children {nd.i}, outpipes={len(nd.outpipes)}')
         # nd.child_nodes.append(nd.Node(nd.outpipe[-1],self,debug=4,epsilon=2000))
         # self.pid_nodeloops.append(self.executor._start(nd.outpipes[-1].find_cover_loop,f'Cover Loop {nd.i}')
      #self.pid_split_loop=self.executor._start(nd.splits_loop,f'Cover Loop {nd.i}')

class FileStreamer: 
   def __init__(self,filename:str,pipe0:pipe,loop_counter:list,executor:LoopExecutor):
      self.filename=filename
      self.pipe0=pipe0
      self.loop_counter=loop_counter
      self.executor=executor
      with open(filename,'rb') as in_handle:
         import numpy as np
         self.data=np.load(in_handle,allow_pickle=True)
      logger.info('__init__')
      
   def file_loop(self,filename:str, loop_counter:list):
     
      try:
         while True:
            self.loop_counter[0]+=1
            state=self.pipe0.put(self.data)
            logger.info(f'file_streamer put returned {state}   data.shape={self.data.shape}')

      except Exception as exc:
            log.exception(f'exception {exc}') 
      return False

   def _start(self):
      try:
         self.pid_file_loop=self.executor.start_thread(self.file_loop,'File Streamer')
         return self.pid_file_loop
      except Exception as exc:
         logger.exception(f'exception {exc}')
if __name__=='__main__':


   executor=LoopExecutor()
   inpipe=pipe(block_size=100)
   loop_counter=[0]
   fileStreamer=FileStreamer('../../data/square.npy',inpipe,loop_counter,executor)
   fileStreamer._start()
   logger.warning(f'fileStreamer={fileStreamer}',executor_list={str(executor.futures)})
   
   #nw=NodeWrapper(node=None,name='test',outpipes=None)
   #pipe0=pipe(block_size=nw.block_size)
   
   #self.pid_file_loop=self.executor._start(self.file_streamer,'File Streamer')


  