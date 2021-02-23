import math

from Model import Model


def solve(problem):
    # Create relaxed version of the model and solve it
    relaxed_model = Model(problem, {
        'all_links_open': True,
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


def get_v_bounds(problem):
    v_bounds = {(i, j): {'lb': math.floor(problem.solution['v'][(i, j)]),
                         'ub': math.ceil(problem.solution['v'][(i, j)])}
                for (i, j) in problem.links}
    return v_bounds
