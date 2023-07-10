# Overall design of the probabilistic cover tree

## Node   
The core code is in **Node** and exposes the following main methods:
* find_cover_loop   - finds a cover for data coming in from a pipe.
* split_loop - split data coming from a pipe into streams, one for each centroid, 
            and send them through output pipes.

A node has a state which is one of the following:
* 0 - running find_cover_loop
* 1 - Waiting for split_loop to be constructed
* 2 - running split_loop
    
### details
given n input stream, add prototypes that are further than
epsilon from all existing prototypes. Stops if gap between
consecutive additions is larger than X. If this does not happen
after a total of Y examples, declares node "high-D".  When stop,
use all accumulated examples to design a balanced partitioner.

## Tree

**Tree** is the central coordinator, or "main()" of the PCT.

The main data structure it holds is the processing tree where the nodes are find_cover_loop or split loop and the edges are pipes.
* This starts as a single node with a pipe that reads data from a file.
* When a node, running as a find_cover_loop, finds a cover, the loop is terminated and a call back is made to the tree, the 
  tree then creates a pipe and a node for each child, and then restarts the original node with a split loop that is connected to 
  the new children nodes via the corresponding nodes.
* the tree is built one layer at a time. The assumption is that all of the find_cover_loops terminate, either by finding a cover or by reaching the conclusion that the cover is too large, creating 
  an unexpended "sink" node.

  The loops are executed as threads managed by a **LoopExecutor**.

  The background activity of the tree is to monitor the tree and check that all of the nodes are functioning.

## class pipe:
    
## class LoopExecutor:    
    
## class Tree:
This is the master coordinator part of the probabilistic cover tree

it's main job is to creates nodes and pipes and connect them to each other

Process for a node:
create an input pipe
create a node and let it run (node_loop)           mode=0
when node has found a cover (found=false) create pipes to children mode=1
send the pipes to the node and change it's mode to pass through. mode=2

Create children nodes.   


