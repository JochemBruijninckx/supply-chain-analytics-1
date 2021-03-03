from Problem import Problem, gen_instance
from Solver import *


# Task to run
# --------------------------------------------------------------------------------------
instance_name = 10    # Enter a number to generate a random instance
method = 'heuristic'                     # Options are 'read', 'solve', 'heuristic'

# Task settings (only used if method is 'heuristic')
# --------------------------------------------------------------------------------------
create_initial_solution = True
heuristic_settings = {
    'step_1': {
        'epsilon': 0.001,
        'surpress_gurobi': True
    },
    'step_2': {
        'start_capacity': 2.5,
        'capacity_step': 0.25
    },
    'step_3': {},
    'step_4': {
        'epsilon': 0.01,
        'surpress_gurobi': True
    }
}

# Function calls
# --------------------------------------------------------------------------------------
if instance_name not in ['small_data_set', 'large_data_set']:
    # This function can be called to generate an .xlsx instance file
    gen_instance(seed=int(instance_name),
                 num_s=5,
                 num_d=5,
                 num_c=10,
                 num_p=1,
                 T=20)
    instance_name = str(instance_name)

# Read and create problem
problem = Problem(instance_name)

# Solve it using the heuristic and display the solution
if method == 'read':
    problem.read_solution(instance_name)
elif method == 'solve':
    problem = solve(problem)
elif method == 'heuristic':
    problem = heuristic(problem, heuristic_settings, create_initial_solution)

# Log functions for solution
# --------------------------------------------------------------------------------------
problem.log_objective(summary_only=True)
problem.display()
input('Press enter to exit..')
