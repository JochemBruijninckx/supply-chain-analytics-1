import csv
import os
import pandas as pd
import numpy as np

from Display import Display


def gen_instance(seed, num_s, num_d, num_c, num_p, T):
    np.random.seed(seed)
    n = num_s + num_d + num_c
    coordinates = (1 / 10) * np.random.randint(0, 10 * n, (n, 2))
    # Sheet 1 - Suppliers
    supplier_data = pd.DataFrame(index=['S' + str(i + 1) for i in range(num_s)],
                                 columns=['LocationX', 'LocationY'])
    supplier_data.index.name = 'SupplierID'
    loc_index = 0
    for i in range(num_s):
        supplier_data.loc['S' + str(i + 1), :] = [coordinates[loc_index][0], coordinates[loc_index][1]]
        loc_index += 1
    print(supplier_data)
    # Sheet 2 - Depots
    depot_data = pd.DataFrame(index=['D' + str(i + 1) for i in range(num_d)],
                              columns=['LocationX', 'LocationY', 'Capacity', 'Holding Cost'])
    depot_data.index.name = 'DepotID'
    for i in range(num_d):
        capacity = round(7 + 20 * np.random.random(), 2)
        holding_cost = round(0.3 + 0.3 * np.random.random(), 2)
        depot_data.loc['D' + str(i + 1), :] = [coordinates[loc_index][0], coordinates[loc_index][1],
                                               capacity, holding_cost]
        loc_index += 1
    print(depot_data)
    # Sheet 3 - Customers
    customer_data = pd.DataFrame(index=['C' + str(i + 1) for i in range(num_c)],
                                 columns=['LocationX', 'LocationY'])
    customer_data.index.name = 'CustomerID'
    for i in range(num_c):
        customer_data.loc['C' + str(i + 1), :] = [coordinates[loc_index][0], coordinates[loc_index][1]]
        loc_index += 1
    print(customer_data)
    # Sheet 4 - Products
    product_data = pd.DataFrame(index=['P' + str(i + 1) for i in range(num_p)],
                                columns=['Size'])
    product_data.index.name = 'ProductID'
    for i in range(num_p):
        product_data.loc['P' + str(i + 1), :] = round(0.2 + 0.8 * np.random.random(), 2)
    print(product_data)
    # Sheet 5 - Links
    origins = ['S' + str(i + 1) for i in range(num_s)] + ['D' + str(i + 1) for i in range(num_d)]
    destinations = ['D' + str(i + 1) for i in range(num_d)] + ['C' + str(i + 1) for i in range(num_c)]
    link_data = pd.DataFrame(index=pd.MultiIndex.from_product([origins, destinations]),
                             columns=['Opening Cost', 'Capacity Cost', 'Duration'])
    link_data.index.names = ['Origin', 'Destination']

    # Determine all distances
    links = [(i, j) for i in origins for j in destinations]
    locations = pd.concat([supplier_data.iloc[:, :3].rename(columns={'SupplierID': 'Location'}),
                           depot_data.iloc[:, :3].rename(columns={'DepotID': 'Location'}),
                           customer_data.iloc[:, :3].rename(columns={'CustomerID': 'Location'})])
    distance = {a: np.hypot(locations.loc[a[0]]['LocationX'] - locations.loc[a[1]]['LocationX'],
                            locations.loc[a[0]]['LocationY'] - locations.loc[a[1]]['LocationY']) for a in links}
    bins = [np.quantile(list(distance.values()), q) for q in [0.25, 0.5, 0.75]]
    durations = np.digitize(list(distance.values()), bins)
    link_index = 0
    for i in origins:
        for j in destinations:
            opening_cost = round(50 + 100 * np.random.random(), 2)
            capacity_cost = round(5 + 10 * np.random.random(), 2)
            duration = np.random.randint(1, 4)
            link_data.loc[i, j] = [opening_cost, capacity_cost, durations[link_index] + 1]
            link_index += 1
    print(link_data)
    # Sheet 6 - Demand
    demand_data = pd.DataFrame(index=pd.MultiIndex.from_product([['C' + str(i + 1) for i in range(num_s)],
                                                                 ['P' + str(j + 1) for j in range(num_p)],
                                                                 ['T' + str(t) for t in range(5, T + 1)]], ),
                               columns=['Amount'])
    demand_data.index.names = ['Customer', 'Product', 'Time']
    for i in range(1, num_c + 1):
        for j in range(1, num_p + 1):
            for t in range(5, T + 1):
                if np.random.random() > 0.7:
                    demand_data.loc['C' + str(i), 'P' + str(j), 'T' + str(t)] = round(18 * np.random.random(), 2)
                else:
                    demand_data.loc['C' + str(i), 'P' + str(j), 'T' + str(t)] = 0
    print(demand_data)
    # Sheet 7 - Backlogs
    backlog_data = pd.DataFrame(index=pd.MultiIndex.from_product([['C' + str(i + 1) for i in range(num_c)],
                                                                  ['P' + str(j + 1) for j in range(num_p)]]),
                                columns=['Amount'])
    backlog_data.index.names = ['Customer', 'Product']
    for i in range(num_c):
        for j in range(num_p):
            backlog_data.loc['C' + str(i + 1), 'P' + str(j + 1)] = round(7 + 10 * np.random.random(), 2)
    print(backlog_data)
    # Sheet 8 - Production
    production_data = pd.DataFrame(index=pd.MultiIndex.from_product([['S' + str(i + 1) for i in range(num_s)],
                                                                     ['P' + str(j + 1) for j in range(num_p)]]),
                                   columns=['Minimum', 'Maximum'])
    production_data.index.names = ['Supplier', 'Product']
    for i in range(num_s):
        for j in range(num_p):
            min_production = round(7 + 10 * np.random.random(), 2)
            max_production = round(min_production + 5 + 5 * np.random.random(), 2)
            production_data.loc['S' + str(i + 1), 'P' + str(j + 1)] = [min_production, max_production]
    print(production_data)
    # Sheet 9 - Parameters
    parameter_data = pd.DataFrame(index=['Truck Size', 'Start Time Horizon', 'End Time Horizon'],
                                  columns=['Value'])
    parameter_data.index.name = 'Parameter'
    parameter_data.loc['Truck Size', :] = round(1 + 2 * np.random.random(), 2)
    parameter_data.loc['Start Time Horizon', :] = 'T1'
    parameter_data.loc['End Time Horizon', :] = 'T' + str(T)
    print(parameter_data)

    with pd.ExcelWriter('Instances/' + str(seed) + '.xlsx') as writer:
        supplier_data.to_excel(writer, sheet_name='Suppliers', merge_cells=False)
        depot_data.to_excel(writer, sheet_name='Depots', merge_cells=False)
        customer_data.to_excel(writer, sheet_name='Customers', merge_cells=False)
        product_data.to_excel(writer, sheet_name='Products', merge_cells=False)
        link_data.to_excel(writer, sheet_name='Links', merge_cells=False)
        demand_data.to_excel(writer, sheet_name='Demand', merge_cells=False)
        backlog_data.to_excel(writer, sheet_name='Backlog Penalty', merge_cells=False)
        production_data.to_excel(writer, sheet_name='Production', merge_cells=False)
        parameter_data.to_excel(writer, sheet_name='Parameters', merge_cells=False)


class Problem:

    def __init__(self, filename):
        # Werkt als je de dataset in dezelfde folder hebt staan als dit bestand (en de dataset onder dezelfde naam
        # hebt staan)
        cwd = os.getcwd()
        filename = os.path.join(cwd, 'Instances/' + filename)
        data = pd.read_excel(filename, sheet_name=None)

        # Data extraction
        # --------------------------------------------------------------------------------------
        self.supplier_data = data['Suppliers']
        self.depot_data = data['Depots']
        self.customer_data = data['Customers']
        self.product_data = data['Products']
        self.link_data = data['Links']
        self.demand_data = data['Demand']
        self.backlog_data = data['Backlog Penalty']
        self.production_data = data['Production']
        self.parameter_data = data['Parameters']
        self.truck_size = data['Parameters']['Value'][0]

        # Nu de data is voorbereid gaan we de sets aanmaken voor onze parameters EN onze decision variables
        self.S = self.supplier_data['SupplierID'].to_list()
        self.D = self.depot_data['DepotID'].to_list()
        self.C = self.customer_data['CustomerID'].to_list()
        self.S_and_D = self.S + self.D
        self.D_and_C = self.D + self.C
        self.P = self.product_data['ProductID'].to_list()
        self.start = int(self.parameter_data['Value'][1].replace('T', ''))
        self.end = int(self.parameter_data['Value'][2].replace('T', ''))
        self.T = [t for t in range(self.start, self.end + 1, 1)]  # Nog niet zeker over deze notatie
        self.links = [(self.link_data['Origin'][i], self.link_data['Destination'][i]) for i in
                      range(len(self.link_data))]
        self.customer_product_time = [
            (self.demand_data['Customer'][i], self.demand_data['Product'][i], self.demand_data['Time'][i])
            for i in range(len(self.demand_data))]
        self.customer_product = [(self.backlog_data['Customer'][i], self.backlog_data['Product'][i]) for i in
                                 range(len(self.backlog_data))]
        self.supplier_product = [(self.production_data['Supplier'][i], self.production_data['Product'][i])
                                 for i in range(len(self.production_data))]
        self.demand_set = []
        for i in range(len(self.demand_data)):
            self.demand_set.append(
                (self.demand_data['Customer'][i], self.demand_data['Product'][i],
                 int(self.demand_data['Time'][i].replace('T', ''))))

        # Sets die nodig zijn voor de decision variables
        self.link_product_time = []
        for a in self.links:
            for p in self.P:
                for t in self.T:
                    self.link_product_time.append((a[0], a[1], p, t))
        self.link_time = []
        for a in self.links:
            for t in self.T:
                self.link_time.append((a[0], a[1], t))

        self.supplier_product_time = []
        for t in self.T:
            for i in range(len(self.production_data)):
                self.supplier_product_time.append((self.production_data['Supplier'][i],
                                                   self.production_data['Product'][i], t))

        self.depot_product_time = []
        for d in self.D:
            for p in self.P:
                for t in self.T:
                    self.depot_product_time.append((d, p, t))

        self.depot_time = []
        for d in self.D:
            for t in self.T:
                self.depot_time.append((d, t))

        self.customer_product_time = []
        for i in range(len(self.demand_data)):
            self.customer_product_time.append((
                self.demand_data['Customer'][i],
                self.demand_data['Product'][i],
                int(self.demand_data['Time'][i].replace('T', ''))
            ))

        # Nu we de sets hebben gemaakt gaan we door met de parameters aan te maken
        # De distance is hier ook al aangemaakt
        # --------------------------------------------------------------------------------------
        self.holding_cost = {self.D[i]: self.depot_data['Holding Cost'][i] for i in range(len(self.D))}
        self.capacity = {self.D[i]: self.depot_data['Capacity'][i] for i in range(len(self.D))}
        self.product_volume = {self.P[i]: self.product_data['Size'][i] for i in range(len(self.P))}
        self.opening_cost = {self.links[i]: self.link_data['Opening Cost'][i] for i in range(len(self.link_data))}
        self.capacity_cost = {self.links[i]: self.link_data['Capacity Cost'][i] for i in range(len(self.link_data))}
        self.duration = {self.links[i]: self.link_data['Duration'][i] for i in range(len(self.link_data))}
        self.locations = pd.concat([self.supplier_data.iloc[:, :3].rename(columns={'SupplierID': 'Location'}),
                                    self.depot_data.iloc[:, :3].rename(columns={'DepotID': 'Location'}),
                                    self.customer_data.iloc[:, :3].rename(columns={'CustomerID': 'Location'})])
        self.locations.set_index([self.locations['Location']], inplace=True)
        self.distance = {a: np.hypot(self.locations.loc[a[0]]['LocationX'] - self.locations.loc[a[1]]['LocationX'],
                                     self.locations.loc[a[0]]['LocationY'] - self.locations.loc[a[1]]['LocationY']) for
                         a in
                         self.links}
        self.demand = {self.demand_set[i]: self.demand_data['Amount'][i] for i in range(len(self.demand_data))}
        self.backlog_pen = {self.customer_product[i]: self.backlog_data['Amount'][i] for i in
                            range(len(self.backlog_data))}
        self.min_prod = {self.supplier_product[i]: self.production_data['Minimum'][i] for i in
                         range(len(self.production_data))}
        self.max_prod = {self.supplier_product[i]: self.production_data['Maximum'][i] for i in
                         range(len(self.production_data))}

        self.cum_demand = {}
        for c in self.C:
            self.cum_demand[c] = [round(sum(self.demand[c, 'P1', f] for f in range(self.start, t + 1)
                                            if (c, 'P1', f) in self.demand_set), 2) for t in self.T]

        self.solution = {
            'x': {},
            'k': {},
            'l': {},
            'v': {},
            'r': {}
        }

    def inventory(self, i, p, t):
        incoming = sum(
            sum(self.solution['x'][j, i, p, str((f - self.duration[j, i]))] for f in range(self.start, t + 1) if
                f - self.duration[j, i] >= self.start)
            for j
            in self.S_and_D if (j, i) in self.links)
        if i not in self.D:
            # i is a customer, so no outgoing product
            return incoming
        else:
            # i is a depot
            outgoing = sum(
                sum(self.solution['x'][i, j, p, str(f)] for f in range(self.start, t + 1)) for j in self.D_and_C if
                (i, j) in self.links)
            return incoming - outgoing

    def read_solution(self, filename):
        # Read solution
        with open('Solutions/' + filename, newline='\n') as file:
            reader = csv.reader((line.replace('  ', ' ') for line in file), delimiter=' ')
            next(reader)  # Skip header
            for var, value in reader:
                name = tuple(var[2:-1].split(','))
                self.solution[var[0]][name] = float(value)

    def log_k(self):
        k = {}
        for link in self.links:
            if self.solution['l'][link] == 1:
                k[link] = [int(self.solution['k'][link + (str(t),)]) for t in self.T]
        for link, trucks in k.items():
            print(link, trucks)

    def log_solution(self, display, draw_settings):
        for t in self.T:
            display.draw(t, draw_settings)
            print('Time', t)
            print('-' * 70)
            # Depot inventory
            for d in self.D:
                I = self.inventory(d, 'P1', t)
                print(d, '| Inventory:', round(I, 2), '(Capacity', str(round(self.capacity[d] /
                                                                             self.product_volume['P1'], 2)) + ')')
            # Customer inventory
            for c in self.C:
                I = self.inventory(c, 'P1', t)
                print(c, '| Inventory:', round(I, 2))

            print('-' * 70)
            # Supplier production
            for s in self.S:
                production = sum([self.solution['x'][(s, j, 'P1', str(t))] for j in self.D_and_C])
                print(s, '| Production:', round(production, 2), '(Min', self.min_prod[(s, 'P1')],
                      'Max', str(self.max_prod[(s, 'P1')]) + ')')
            print('-' * 70)
            # Outgoing transport
            print('Outgoing transport:')
            for i in self.S_and_D:
                for j in self.D_and_C:
                    if i is not j:
                        transport = self.solution['x'][(i, j, 'P1', str(t))]
                        if transport > 0:
                            print(i, '->', j, '| Units:', round(transport, 2))
            print('-' * 70)
            # Arriving transport
            print('Arriving transport:')
            for f in range(1, t + 1):
                for i in self.S_and_D:
                    for j in self.D_and_C:
                        if i is not j:
                            # Check if transport would arrive now
                            if f + self.duration[(i, j)] == t:
                                transport = self.solution['x'][(i, j, 'P1', str(f))]
                                if transport > 0:
                                    print(i, '->', j, '| Units:', round(transport, 2), '(Sent at time', str(f) + ')')

            input('Press enter to continue..')
            print()


    def display(self):
        disp = Display(self)
        disp.draw(0, {})
        input('Press enter to continue..')

