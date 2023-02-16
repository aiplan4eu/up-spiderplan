# up-spiderplan
A constraint-based planning engine for unified planning.

## Roadmap

### 0.1.0 Basic UP Support

- [x] UP problems can be converted to constraint databases
  - [x] Classical plannning
- [x] Call spiderplan to produce a solution/failure
- [x] Answer translated to a UP result

### 0.2.0 Motion Planning

- [x] Motion planning constraints extracted from UP problem 
- [x] Solve problem with motion constraints and get a plan with paths
- [ ] Fix Spiderplan motion planner to use correct motion model
- [ ] Allow configuration with available motion planning algorithms
- [ ] Convert plan into UP plan with motion

### 0.3.0 Running the Engine in the UP
 
- [ ] Fix spiderplan grpc server in docker
- [ ] Use docker to run server through up-spiderplan
- [ ] Local install of spiderplan as a UP engine

### 0.x.0

- Temporal planning
- Spiderplan configuration through UP

