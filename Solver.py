import math

from Model import Model


def solve(problem, settings=None, bounds=None):
    # Create regular model
    model = Model(problem, settings, bounds=bounds)
    model.solve(problem.instance_name)
    # Load the solution into our problem object
    problem.read_solution(problem.instance_name)


def heuristic(problem):
    # Create relaxed version of the model and solve it
    relaxed_model = Model(problem, {
        'all_links_open': True,
        'non_integer_trucks': True,
        'linear_backlog_approx': True
    })
    relaxed_model.write(problem.instance_name + '_relaxed')
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
        'linear_backlog_approx': True
    }, bounds=bounds)
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


def get_utilization_costs(problem):
    utilization_costs = {}
    for link in problem.links:
        if link in problem.solution['v']:
            v = problem.solution['v'][link]
            if v > 0:
                link_costs = problem.opening_cost[link] + problem.capacity_cost[link] * v
                link_utilization = sum([problem.product_volume[p] * problem.solution['x'][link[0], link[1], p, str(t)]
                                        for p in problem.P for t in problem.T])
                utilization_costs[link] = link_costs / link_utilization
    utilization_costs = dict(sorted(utilization_costs.items(), key=lambda item: item[1]))
    return utilization_costs
