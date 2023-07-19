from Problem import Problem, gen_instance
from Solver import *


# Task to run
# --------------------------------------------------------------------------------------
instance_name = 'small_data_set_2022'   # Enter a number to generate a random instance
method = 'solve'                     # Options are 'read', 'solve', 'heuristic'

# Task settings (only used if method is 'heuristic')
# --------------------------------------------------------------------------------------
create_initial_solution = True
heuristic_settings = {
    'model_parameters': {
        'boundary': 10,
        'delta': 0.25,
    },
    'step_1': {
        'epsilon': 0.001,
        'surpress_gurobi': False
    },
    'step_2': {
        'start_capacity': 2.5,
        'capacity_step': 0.25
    },
    'step_3': {
        'check_full_list': False
    },
    'step_4': {
        'epsilon': 0.01,
        'surpress_gurobi': False
    }
}

# Function calls
# --------------------------------------------------------------------------------------
if instance_name not in ['small_data_set', 'large_data_set', 'small_data_set_2022']:
    # This function can be called to generate an .xlsx instance file
    gen_instance(seed=int(instance_name),
                 num_s=6,
                 num_d=8,
                 num_c=16,
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
# problem.verify_constraints()
# problem.log_solution()
problem.log_backlog()
problem.log_objective(summary_only=True)
problem.display()
input('Press enter to exit..')
