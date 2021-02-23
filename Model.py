import gurobipy as gb


class Model:
    def __init__(self, problem, settings, bounds=None):
        if bounds is None:
            bounds = {}
        # Model setup
        # --------------------------------------------------------------------------------------
        mdl = gb.Model()

        # Objective
        tot_opening_cost = gb.LinExpr()
        tot_capacity_cost = gb.LinExpr()
        tot_distance_cost = gb.LinExpr()
        tot_holding_cost = gb.LinExpr()
        tot_backlog_cost = gb.QuadExpr()

        # Variables
        # --------------------------------------------------------------------------------------
        x = mdl.addVars(problem.link_product_time, vtype=gb.GRB.CONTINUOUS, lb=0, name='x')
        r = mdl.addVars(problem.supplier_product_time, vtype=gb.GRB.BINARY, name='r')
        if not settings['all_links_open']:
            l = mdl.addVars(problem.links, vtype=gb.GRB.BINARY, name='l')
        if settings['non_integer_trucks']:
            k = mdl.addVars(problem.link_time, vtype=gb.GRB.CONTINUOUS, lb=0, name='k')
            v = mdl.addVars(problem.links, vtype=gb.GRB.CONTINUOUS, lb=0, name='v')
        else:
            k = mdl.addVars(problem.link_time, vtype=gb.GRB.INTEGER, lb=0, name='k')
            v = mdl.addVars(problem.links, vtype=gb.GRB.INTEGER, lb=0, name='v')

        # Set bounds if provided
        if 'r' in bounds:
            for (s, p, t) in bounds['r'].keys():
                r[s, p, int(t)].lb = bounds['r'][(s, p, t)]
                r[s, p, int(t)].ub = bounds['r'][(s, p, t)]

        # Objective
        # --------------------------------------------------------------------------------------
        if not settings['all_links_open']:
            tot_opening_cost += gb.quicksum(problem.opening_cost[i, j] * l[i, j] for i, j in problem.links)

        tot_capacity_cost += gb.quicksum(problem.capacity_cost[i, j] * v[i, j] for i, j in problem.links)
        tot_distance_cost += gb.quicksum(k[i, j, t] * problem.distance[i, j] for i, j, t in problem.link_time)

        def inventory_depot(d, p, t):
            incoming = gb.quicksum(
                gb.quicksum(x[i, d, p, (f - problem.duration[i, d])] for f in range(problem.start, t + 1) if
                            f - problem.duration[i, d] >= problem.start)
                for i
                in problem.S_and_D if (i, d) in problem.links)
            outgoing = gb.quicksum(
                gb.quicksum(x[d, j, p, f] for f in range(problem.start, t + 1)) for j in problem.D_and_C if
                (d, j) in problem.links)
            return incoming - outgoing

        tot_holding_cost += gb.quicksum(
            gb.quicksum(
                problem.holding_cost[d] * gb.quicksum(
                    problem.product_volume[p] * inventory_depot(d, p, t) for p in problem.P) for d in problem.D) for t in
            problem.T)

        def verschil_customer(c, p, t):
            ontvangst = gb.quicksum(
                gb.quicksum(x[i, c, p, f - problem.duration[i, c]] for f in range(problem.start, t + 1) if
                            f - problem.duration[i, c] >= problem.start) for
                i in
                problem.S_and_D if (i, c) in problem.links)
            cum_demand = gb.quicksum(
                problem.demand[c, p, f] for f in range(problem.start, t + 1) if (c, p, f) in problem.demand_set)
            return ontvangst - cum_demand

        if not settings['perfect_delivery']:
            tot_backlog_cost += gb.quicksum(
                gb.quicksum(
                    problem.backlog_pen[c, p] * (verschil_customer(c, p, t) ** 2) for c, p in problem.customer_product) for
                t in
                problem.T)

        mdl.setObjective(tot_opening_cost + tot_capacity_cost + tot_distance_cost + tot_holding_cost + tot_backlog_cost,
                         gb.GRB.MINIMIZE)

        # Constraints
        # --------------------------------------------------------------------------------------
        # Truck capacity on links
        mdl.addConstrs(k[i, j, t] <= v[i, j] for i, j, t in problem.link_time)
        # Sufficient amount of trucks for transport size
        mdl.addConstrs(
            k[i, j, t] >= (gb.quicksum(problem.product_volume[p] * x[i, j, p, t] for p in problem.P) / problem.truck_size)
            for i, j, t in problem.link_time)
        # Linking constraint for opening of links
        if not settings['all_links_open']:
            mdl.addConstrs(10000 * l[i, j] >= v[i, j] for i, j in problem.links)
        # Minimum production constraint for suppliers
        mdl.addConstrs(
            gb.quicksum(x[s, j, p, t] for j in problem.D_and_C if (s, j) in problem.links) >=
            problem.min_prod[s, p] * r[s, p, t] for s, p, t in problem.supplier_product_time)
        # Maximum production constraint for suppliers
        mdl.addConstrs(
            gb.quicksum(x[s, j, p, t] for j in problem.D_and_C if (s, j) in problem.links) <=
            problem.max_prod[s, p] * r[s, p, t] for s, p, t in problem.supplier_product_time)
        # Capacity constraint for depots
        mdl.addConstrs(
            gb.quicksum(problem.product_volume[p] * inventory_depot(d, p, t) for p in problem.P) <= problem.capacity[d] for
            d, t in problem.depot_time)
        # Cannot transport more from depots than is in their inventories
        mdl.addConstrs(
            gb.quicksum(x[d, j, p, t] for j in problem.D_and_C if j != d and (d, j) in problem.links) <=
            inventory_depot(d, p, t) for d, p, t in problem.depot_product_time)
        # All demand must be filled by end of period
        mdl.addConstrs(gb.quicksum(
            gb.quicksum(
                x[i, c, p, t - problem.duration[i, c]] for t in problem.T if t - problem.duration[i, c] >= problem.start)
            for i in problem.S_and_D if
            (i, c) in problem.links) == gb.quicksum(
            problem.demand[c, p, t] for t in problem.T if (c, p, t) in problem.demand_set) for c, p in
                       problem.customer_product)
        # No backlog constraint
        if settings['perfect_delivery']:
            mdl.addConstrs(
                problem.demand[c, p, t] == gb.quicksum(x[i, c, p, t - problem.duration[i, c]] for i in problem.S_and_D
                                                       if t - problem.duration[i, c] >= problem.start
                                                       )
                for c, p, t in problem.demand_set
            )

        # Generate model
        mdl.update()

        self.mdl = mdl
        # mdl.optimize()
        #
        # print('Opening cost:', tot_opening_cost.getValue())
        # print('Capacity cost:', tot_capacity_cost.getValue())
        # print('Distance cost:', tot_distance_cost.getValue())
        # print('Holding cost:', tot_holding_cost.getValue())
        # print('Backlog cost:', tot_backlog_cost.getValue())

    # Solve model and save solution to a solution file
    def solve(self, instance_name):
        # Optimize
        self.mdl.optimize()
        # Save solution
        self.mdl.write('Solutions/' + instance_name + '.sol')
