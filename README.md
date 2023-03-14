# up-spiderplan

A constraint-based planning engine for unified planning.

## Try it out!

Note: This will become more compact later. 

Note: This requires a `docker` and `docker-compose` to be installed.


Create and activate a Python 3.7 environment. Here we use conda:

    conda create --name up-sp-test python=3.7
    conda activate up-sp-test
    
Install the Unified Planning library with the TAMP branch:

    git clone https://github.com/aiplan4eu/unified-planning.git
    cd unified-planning
    git checkout add-tamp
    pip install -e .
    cd ..


Install up-spiderplan from pypi test repository:
    
    pip install -i https://test.pypi.org/simple/ --extra-index-url https://pypi.org/simple up-spiderplan
    
    
Clone the up-spiderplan repository to get a test case:
    
    git clone https://github.com/aiplan4eu/up-spiderplan.git
    cd up-spiderplan
    pip install -r requirements.txt
    
Finally, we can run the test: 

    python up_spiderplan/test.py
    
This will build and run a docker container that hosts the spiderplan
server. Therefore it will take a bit of time on the first run.

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

## Issues

- [x] Waiting for docker container does not work
