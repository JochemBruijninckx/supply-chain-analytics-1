from Problem import Problem, gen_instance
from Solver import *

# This function can be called to generate an .xlsx instance file
# seed = 208
# gen_instance(seed=seed,
#              num_s=3,
#              num_d=2,
#              num_c=4,
#              num_p=1,
#              T=20)

# Read and create problem
instance_name = 'small_data_set'
problem = Problem(instance_name)
# Solve it using the heuristic and display the solution
solve(problem)
problem.log_k()
problem.display()
problem.log_solution()
