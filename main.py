from Problem import Problem, gen_instance
from Solver import *


# Settings
# --------------------------------------------------------------------------------------
instance_name = 404    # Enter a number to generate a random instance
method = 'heuristic'                     # Options are 'read', 'solve', 'heuristic'

# Function calls
# --------------------------------------------------------------------------------------
if instance_name not in ['small_data_set', 'large_data_set']:
    # This function can be called to generate an .xlsx instance file
    gen_instance(seed=int(instance_name),
                 num_s=7,
                 num_d=12,
                 num_c=20,
                 num_p=1,
                 T=40)
    instance_name = str(instance_name)

# Read and create problem
problem = Problem(instance_name)

# Solve it using the heuristic and display the solution
if method == 'read':
    problem.read_solution(instance_name)
elif method == 'solve':
    solve(problem)
elif method == 'heuristic':
    heuristic(problem, create_initial_solution=True)

# Log functions for solution
# --------------------------------------------------------------------------------------
