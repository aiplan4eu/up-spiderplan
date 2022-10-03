# up-spiderplan
A constraint-based planning engine for unified planning.

## Roadmap

### 0.1.0

- UP problems can be converted to constraint databases
  - Assume no real-valued fluents
- Call spiderplan to produce a solution/failure
- Answer translated to a UP result

### 0.2.0

- Motion planning constraints extracted from UP problem 

### 0.3.0

- Resource constraints extracted from UP problem

### 0.4.0

- Spiderplan configuration through UP

## Notes

### Real-valued Fluents

- See "robot" example in UP repository
- Handle through dedicated constraint-type and solver/propagator
- Detect based on UP type 
- Replace all usages of real-valued fluents by corresponding constraints
