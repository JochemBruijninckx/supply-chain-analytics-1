import numpy as np


def get_v_bounds(problem):
    v_bounds = {
        link: {'lb': 0, 'ub': np.inf} for link in problem.links
    }
    # Upper bounds for suppliers
    max_production_volume = {
        s: sum(problem.product_volume[p] * problem.max_prod[(s, p)] for p in problem.P if (s, p) in problem.max_prod)
        for s in problem.S
    }
    for s in problem.S:
        bound = np.ceil(max_production_volume[s] / problem.truck_size)
        for j in problem.D_and_C:
            if v_bounds[(s, j)]['ub'] > bound:
                v_bounds[(s, j)]['ub'] = bound

    # Upper bounds for depots
    for d in problem.D:
        bound = np.ceil(problem.capacity[d] / problem.truck_size)
        for j in problem.D_and_C:
            if d is not j:
                if v_bounds[(d, j)]['ub'] > bound:
                    v_bounds[(d, j)]['ub'] = bound

    min_production_volume = {
        (s, p): problem.product_volume[p] * problem.min_prod[(s, p)] for (s, p) in problem.supplier_product
    }
    # Required capacity to use production at a supplier
    required_supplier_capacity = {
        (s, p): np.ceil(min_production_volume[(s, p)] / problem.truck_size) for (s, p) in problem.supplier_product
    }

    print('Simple bounds')
    print('-' * 70)
    for link, bounds in v_bounds.items():
        print(link, bounds)

    # Required capacity to possibly deliver all orders without backlog
    required_capacity_no_backlog = {
        c: np.ceil(max([problem.product_volume[p] * problem.demand[(c, p, t)] for p in problem.P for t in problem.T
                        if (c, p, t) in problem.demand]) / problem.truck_size) for c in problem.C
    }


    print('No backlog bounds')
    print('-' * 70)
    for key, value in required_capacity_no_backlog.items():
        print(key, value)


    print('Minimum supplier bounds')
    print('-' * 70)
    for key, value in required_supplier_capacity.items():
        print(key, value)
