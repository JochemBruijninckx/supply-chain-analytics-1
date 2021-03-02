from Problem import Problem, gen_instance
from Solver import *

# This function can be called to generate an .xlsx instance file
# seed = 212
# gen_instance(seed=seed,
#              num_s=2,
#              num_d=1,
#              num_c=2,
#              num_p=1,
#              T=20)

# Read and create problem
instance_name = 'small_data_set'
problem = Problem(instance_name)

# Solve it using the heuristic and display the solution
# problem.read_solution(instance_name)
solve(problem)
print(get_utilization_costs(problem))
# problem.log_backlog()
problem.log_objective()
problem.display()
# problem.log_solution()
# problem.log_k()