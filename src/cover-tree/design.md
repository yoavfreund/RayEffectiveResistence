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
    
## class NodeWrpper:    
    
"This is the function that implements the control of the tree.

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

 

## class Tree:
This is the master coordinator part of the probabilistic cover tree

it's main job is to creates nodes and pipes and connect them to each other

Process for a node:
create an input pipe
create a node and let it run (node_loop)           mode=0
when node has found a cover (found=false) create pipes to children mode=1
send the pipes to the node and change it's mode to pass through. mode=2

Create children nodes.   


## interface to solver
The tree outputs, for each level of the tree, a weighted epsilon cover, which is a list of 
pairs(X,w) where X is the centroid represented as an array and w is the weight (fraction of examples that fall in bin)

In addition, the tree exposes an interface for finding the near neighbors of a centroid:
Input: a center C, a level in the tree, max distance
output: all of the centers within the level of the tree that are at most max distance from C.
For each center, the output is the point and the distance from C to the point.