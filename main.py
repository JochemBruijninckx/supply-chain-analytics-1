from Problem import Problem, gen_instance
from Solver import *

# This function can be called to generate an .xlsx instance file
# seed = 10
# gen_instance(seed=seed,
#              num_s=3,
#              num_d=2,
#              num_c=3,
#              num_p=2,
#              T=19)

# Read and create problem
instance_name = 'large_data_set'
problem = Problem(instance_name)
# Solve it using the heuristic and display the solution
solve(problem)
problem.display()
