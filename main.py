import numpy as np
import pandas as pd

import Model
from Display import Display
from Problem import Problem, gen_instance
from Solver import *

draw_settings = {
    'show_capacities': True,
    'show_trucks': False,
    'show_transport': False,
    'show_inventory': False
}

# seed = np.random.randint(100)
#
# gen_instance(seed=seed,
#              num_s=3,
#              num_d=2,
#              num_c=3,
#              num_p=2,
#              T=19)
#
# problem = Problem(str(seed) + '.xlsx')
# mdl = Model.create(problem)
# Model.solve(mdl, str(seed))


model_settings = {
    'all_links_open': False,
    'non_integer_trucks': False,
    'perfect_delivery': True,
    'infinite_production': False
}
instance_name = 'large_data_set'

problem = Problem(instance_name + '.xlsx')
mdl = Model.create(problem, model_settings)
Model.solve(mdl, instance_name)

problem.read_solution(instance_name + '.sol')
problem.log_solution(Display(problem), draw_settings)

# problem = Problem('large_data_set.xlsx')
# get_v_bounds(problem)
# problem.display()


# problem.read_solution('small_data_set.sol')
# problem.log_solution(Display(problem), draw_settings)
# problem.log_k()
