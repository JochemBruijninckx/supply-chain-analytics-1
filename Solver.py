import math

from Model import Model


def solve(problem):
    bounds = None
    # bounds = {'v': get_v_bounds(problem, all_zero=True)}
    # bounds['v'][('D2', 'C1')]['ub'] = 5
    # bounds['v'][('D2', 'C3')]['ub'] = 5
    # bounds['v'][('S1', 'D2')]['ub'] = 5
    # bounds['v'][('S2', 'C2')]['ub'] = 4
    # bounds['v'][('S2', 'D2')]['ub'] = 4
    # Create regular model
    model = Model(problem, bounds=bounds)
    model.solve(problem.instance_name)
    # Load the solution into our problem object
    problem.read_solution(problem.instance_name)


def heuristic(problem):
    # Create relaxed version of the model and solve it
    relaxed_model = Model(problem, {
        'all_links_open': False,
        'non_integer_trucks': True,
        'perfect_delivery': True,
    })
    relaxed_model.solve(problem.instance_name + '_relaxed')
    # Load the solution into our problem object
    problem.read_solution(problem.instance_name + '_relaxed')
    drop_links(problem)
    # Construct bounds to be used in reduced problem
    bounds = {
        'r': problem.solution['r'],
        'v': get_v_bounds(problem)
    }
    # Create reduced, non-relaxed model
    reduced_model = Model(problem, {
        'all_links_open': False,
        'non_integer_trucks': False,
        'perfect_delivery': False,
    }, bounds)
    reduced_model.solve(problem.instance_name)
    # Load the feasible solution into our problem object
    problem.read_solution(problem.instance_name)


def drop_links(problem):
    unused_links = [link for link in problem.links if problem.solution['v'][link] == 0]
    # Remove unused links form all relevant sets
    for link in unused_links:
        problem.links.remove(link)
        for t in problem.T:
            problem.link_time.remove((link[0], link[1], t))
            for p in problem.P:
                problem.link_product_time.remove((link[0], link[1], p, t))


def get_v_bounds(problem, all_zero=False):
    if not all_zero:
        v_bounds = {(i, j): {'lb': math.floor(problem.solution['v'][(i, j)]),
                             'ub': math.ceil(problem.solution['v'][(i, j)])}
                    for (i, j) in problem.links}
    else:
        v_bounds = {(i, j): {'lb': 0,
                             'ub': 0}
                    for (i, j) in problem.links}
    return v_bounds

