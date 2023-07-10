from concurrent.futures import ThreadPoolExecutor
import logging as log
   
logger = log.getLogger('ThreadPool')
logger.setLevel(log.WARNING)
 
class LoopExecutor:   
   
   def __init__(self):
      self.executor=ThreadPoolExecutor(max_workers=1)
      self.futures={}
      self.futures_counter=0
      logger.info('LoopExecutor.__init__')
         
   def loop(self,run_flag:[bool],loop_counter:[int],f,name:str,*args,**kwargs):
      """_summary_

      Args:
          run_flag (list of one boolean): a flag that determines when to run and when to stop
          loop_counter ([int]): _description_
          f (function): the body of the loop
          name (str): _description_
      """

      while run_flag[0]:
         loop_counter[0]+=1
         stop=f(*args,**kwargs)
         if stop:
            run_flag[0]=False
         logger.info(f'LoopExecutor for {name} {loop_counter[0]}, run_flag {run_flag[0]}')
      logger.info(f'loop for {name} stopped')

   def _start(self,f,name,*args,**kwargs): 
      logger.info(f'_start {name}')
      run_flag=[True]
      loop_counter=[0]
      future=self.executor.submit(self.loop,run_flag,loop_counter,f,name,*args,**kwargs)
      self.futures_counter+=1
      self.executor._max_workers=self.futures_counter+1
      self.futures[self.futures_counter]={'run_flag':run_flag,
                                             'future':future,
                                             'name':name,
                                             'loop_counter':loop_counter
                                             }
      return self.futures_counter
   
   def _stop(self,index):
       
      assert index in self.futures
        
        
      logger.info(f'_stop, index={index} name={self.futures[index]["name"]}')
      
      run_flag=self.futures[index]['run_flag']
      run_flag[0]=False


      future=self.futures[index]['future']
      future.cancel()

      return True #code below is for checking if process has actually stopped

#        from time import sleep

#        for i in range(10):
#           if future.cancel():
#              return True
#           sleep(0.01)
#
#        raise Exception('process {} did not stop'.format(index))


if __name__=='__main__':


   from pipe import pipe
   import numpy as np   
   from time import sleep


   Q1=pipe(block_size=3)
   Q2=pipe(block_size=2)

   def P1(Q:pipe):
         print('P1')
         Q.put(np.reshape(np.arange(20),[10,2]))
         sleep(1)

   def P2(Q1:pipe,Q2:pipe):
         print('P2 about to get')
         item=Q1.get(block=False)
         if not item is None:
            print('P2,item shape=',item.shape)
            Q2.put(item)
         sleep(1) 

   def P3(Q:pipe):
   
         print('P3 about to get')
         item=Q.get(block=False)
         if not item is None:
            print('P3 item shape=',item.shape) 
            print(item)
         sleep(1)
      
   P1(Q1)
   loopExecutor=LoopExecutor()
   i2=loopExecutor._start(P2,'P2',Q1,Q2)
   i3=loopExecutor._start(P3,'P3',Q2) 

   sleep(1)
   print('futures1',loopExecutor.futures)
         
   sleep(1)
   print('futures2',loopExecutor.futures)
         
   print('stopping')
   loopExecutor._stop(i3)
   loopExecutor._stop(i2)





