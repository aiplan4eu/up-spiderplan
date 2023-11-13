# Integration of Spiderplan with the Unified Planning Library

A constraint-based planning engine for unified planning.

## Try it out!

**Note:** This requires a `docker` and `docker-compose` to be installed.

Create and activate a Python 3.7 environment. Here we use conda:

    conda create --name up-sp-test python=3.7
    conda activate up-sp-test
    
Install `up-spiderplan`:

    pip install up-spiderplan
    
Clone the up-spiderplan repository to get a test case:
    
    git clone https://github.com/aiplan4eu/up-spiderplan.git
    cd up-spiderplan
    
Finally, we can run the test: 

    python tests/test.py
    
This will build and run a docker container that hosts the spiderplan
server. Therefore it will take a bit of time on the first run.

## Default Configuration

Spiderplan solves hybrid planning problems by combining preprocessors, propagators and solvers for all required constraint types.
Temporal propgatation is needed even for classical planning because under the hood Spiderplan is a temporal interval based planner.

- *Search space:* graph
- *Heuristic:* Fast forward
- *Preprocessors:* temporal propagation, constraints processing and operator grounding. 
- *Propagators:* pruning, domain constraints, temporal constraints, motion planning
- *Solvers:* constraint processing, forward goal resolver

## Planning Approaches of UP supported

Combined task and motion planning with Reeds Shepp car motion model. 

## Operation Modes

Oneshot planning

## Roadmap

### 0.1.0 Basic UP Support

- [x] UP problems can be converted to constraint databases
  - [x] Classical plannning
- [x] Call spiderplan to produce a solution/failure
- [x] Answer translated to a UP result

### 0.2.0 Motion Planning

- [x] Motion planning constraints extracted from UP problem 
- [x] Solve problem with motion constraints and get a plan with paths
- [x] Fix Spiderplan motion planner to use correct motion model
- [x] Allow configuration with available motion planning algorithms
- [x] Convert plan into UP plan with motion

### 0.3.0 Running the Engine in the UP
 
- [x] Fix spiderplan grpc server in docker
- [x] Use docker to run server through up-spiderplan

### 0.4.0 Fixes for Unified Planning 1.0.0 and UP test cases

- UP dependency
- Removed circular dependency which makes it impossible to load up-spiderplan as a up engine.
- Fixed EngineImpl to extend OneShotMixin

### 0.5.0 Added Internal Engine Time to Result Metric

- Adding internal engine time to result metric

### 0.5.1 Fixes

- Removed letter 's' from reported times
- Fixed issue with new UP test cases

## Issues

- [x] Waiting for docker container does not work
