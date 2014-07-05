#! /usr/env python

# The MIT License (MIT)

# Copyright (c) 2013, 2014 Erik Hemberg

# Permission is hereby granted, free of charge, to any person
# obtaining a copy of this software and associated documentation files
# (the "Software"), to deal in the Software without restriction,
# including without limitation the rights to use, copy, modify, merge,
# publish, distribute, sublicense, and/or sell copies of the Software,
# and to permit persons to whom the Software is furnished to do so,
# subject to the following conditions:

# The above copyright notice and this permission notice shall be
# included in all copies or substantial portions of the Software.

# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND,
# EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF
# MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND
# NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS
# BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN
# ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN
# CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.
import csv

import random
import math
import copy
import argparse

"""Genetic Programming
===================


Implementation of GP to describe how the algorithm works. For teaching
purposes.  The functions are aimed to be as simple and self contained
as possible. See oop_pony_gp for complex functions and object
orientation could reduce the number of lines.

An individual is a dictionary with two keys:

  - *Genome* -- A tree
  - *Fitness* -- The fitness of the evaluated tree


Fitness Function
----------------

Find a symbolic expression (function) which yields the lowest error
for a given set of inputs.

Inputs have explanatory variables that have a corresponding
output. The input data is split into test and training data. The
training data is used to generate symbolic expressions and the test
data is used to evaluate the out-of-sample performance of the
evaluated expressions.

.. codeauthor:: Erik Hemberg <hembergerik@csail.mit.edu>

"""
DEFAULT_FITNESS = -1000


def append_node(node, symbol):
    """
    Append a symbol to the node.
    :param node: The node that will be appended to
    :type node: list
    :param symbol: The symbol that is appended
    :type symbol: str
    """

    # Create a list with the symbol and append it to the node
    node.append([symbol])


def grow(node, depth, max_depth, full, symbols):
    """
    Recursively grow a node to max depth in a pre-order, i.e. depth-first
    left-to-right traversal.

    :param node: Root node of subtree
    :type node: list
    :param depth: Current tree depth
    :type depth: int
    :param max_depth: Maximum tree depth
    :type max_depth: int
    :param full: grows the tree to max depth when true
    :type full: bool
    :param symbols: set of symbols to chose from
    :type symbols: dict
    """

    # grow is called recursively in the loop. The loop iterates arity number
    # of times. The arity is given by the node symbol
    for _ in range(symbols["arities"][node[0]]):
        # Get a random symbol
        symbol = get_rnd_symbol(depth, max_depth, symbols, full)
        # Create a child node and append it to the tree
        append_node(node, symbol)
        # Call grow with the child node as the current node
        current_node = node[-1]
        grow(current_node, depth + 1, max_depth, full, symbols)


def get_number_of_nodes(node, cnt):
    """
    Return the number of nodes in the tree. A recursive depth-first
    left-to-right search is done

    #TODO can be made non-recursive for improve readability

    :param node: Root of tree
    :type node: list
    :param cnt: Current number of nodes in the tree
    :type cnt: int
    :return: Number of nodes in the tree
    :rtype: int

    """

    # Increase the count
    cnt += 1
    # Iterate over the children
    for child in node[1:]:
        # Recursively count the child nodes
        cnt = get_number_of_nodes(child, cnt)

    return cnt


def get_node_at_index(root, idx):
    """
    Return the node in the tree at a given index. The index is
    according to a depth-first left-to-right ordering.

    :param root: Root of tree
    :type root: list
    :param idx: Index of node to find
    :type idx: int
    :return: Node at the given index (based on depth-first left-to-right
    indexing)
    :rtype: list

    """

    # Stack of unvisited nodes
    unvisited_nodes = [root]
    # Initial node is the same as the root
    node = root
    # Set the current index
    cnt = 0
    # Iterate over the tree until the index is reached
    while cnt < idx:
        # Take an unvisited node from the stack
        node = unvisited_nodes.pop()
        # Add the children of the node to the stack
        if len(node) > 0:
            # Get the children
            children = node[1:]
            # Reverse the children before appending them to the stack
            children.reverse()
            # Add children to the stack
            unvisited_nodes.extend(children)

        # Increase the current index
        cnt += 1

    return node


def get_max_depth(node, depth, max_depth):
    """
    Return the max depth of the tree. Recursively traverse the tree
    :param node: Root of the tree
    :type node: list
    :param depth: Current tree depth
    :type depth: int
    :param max_depth: Maximum depth of the tree
    :type max_depth: int
    :return: Maximum depth of the tree
    :rtype: int
    """

    # Update the max depth if the current depth is greater
    if max_depth < depth:
        max_depth = depth

    # Traverse the children of the root node
    for child in node[1:]:
        # Increase the depth
        depth += 1
        # Recursively get the depth of the child node
        max_depth = get_max_depth(child, depth, max_depth)
        # Decrease the depth
        depth -= 1

    return max_depth


def get_rnd_symbol(depth, max_depth, symbols, full=False):
    """
    Get a random symbol. The depth determines if a terminal
    must be chosen. If full is specified a function will be chosen
    until the max depth.

    :param depth: Current depth
    :type depth: int
    :param max_depth: Max depth determines if a function symbol can be
    chosen. I.e. a symbol with arity greater than zero
    :type max_depth: int
    :param symbols: The possible symbols.
    :type symbols: dict
    :param full: True if function symbols should be drawn until max depth
    :returns: A random symbol
    :rtype: str

    """

    # Pick a terminal if max depth has been reached
    if depth >= max_depth:
        # Pick a random terminal
        symbol = random.choice(symbols["terminals"])
    else:
        # Can it be a terminal before the max depth is reached
        # then there is 50% chance that it is a terminal
        if not full and bool(random.getrandbits(1)):
            # Pick a random terminal
            symbol = random.choice(symbols["terminals"])
        else:
            # Pick a random function
            symbol = random.choice(symbols["functions"])

    # Return the picked symbol
    return symbol


def sort_population(individuals):
    """
    Return a list sorted on the fitness value of the individuals in
    the population. Descending order.

    :param individuals: The population of individuals
    :type individuals: list
    :return: THe population of individuals sorted by fitness in descending order
    :rtype: list

    """

    # Sort the individual elements on the fitness
    individuals = sorted(individuals, key=lambda x: x['fitness'])
    # Reverse for descending order
    individuals.reverse()

    return individuals


def evaluate_individual(individual, fitness_cases, targets):
    """
    Evaluate fitness based on fitness cases and target values. Fitness
    cases are a set of exemplars (input and output points) by
    comparing the error between the output of an individual(symbolic
    expression) and the target values.

    Attributes:

    - Fitness cases -- Input values for the exemplars
    - Targets -- The target values corresponding to the fitness case
    - Variables -- The current value of the variables in the evaluated exemplar

    Evaluates and sets the fitness in an individual. Fitness is the
    negative mean square error(MSE).

    :param individual: Individual solution to evaluate
    :type individual: dict
    :param fitness_cases: Input for the evaluation
    :type fitness_cases: list
    :param targets: Output corresponding to the input
    :type targets: list

    """

    # Initial fitness value
    fitness = 0.0
    # Calculate the error between the output of the individual solution and
    # the target for each input
    for case, target in zip(fitness_cases, targets):
        # Get output from evaluation function
        output = evaluate(individual["genome"], case)
        # Get the squared error
        error = output - target
        fitness += error * error

    # Get the mean fitness and assign it to the individual
    individual["fitness"] = -fitness / float(len(targets))
    print(individual)


def evaluate(node, case):
    """
    Evaluate a node recursively. The node's symbol is evaluated.

    :param node: Evaluated node
    :type node: list
    :param case: Current fitness case
    :type case: list
    :returns: Value of the evaluation
    :rtype: float
    """
    symbol = node[0]
    # Identify the node symbol
    if symbol == "+":
        # Add the values of the node's children
        return evaluate(node[1], case) + evaluate(node[2], case)

    elif symbol == "-":
        # Subtract the values of the node's children
        return evaluate(node[1], case) - evaluate(node[2], case)

    elif symbol == "*":
        # Multiply the values of the node's children
        return evaluate(node[1], case) * evaluate(node[2], case)

    elif symbol == "/":
        # Divide the value's of the nodes children. Too low values of the
        # denominator returns the numerator
        numerator = evaluate(node[1], case)
        denominator = evaluate(node[2], case)
        if abs(denominator) < 0.00001:
            denominator = 1

        return numerator / denominator

    elif symbol.startswith("x"):
        # Get the variable value
        return case[int(symbol[1:])]

    else:
        # The symbol is a constant
        return float(symbol)


def initialize_population(param):
    """
    Ramped half-half initialization. The individuals in the
    population are initialized using the grow or the full method for
    each depth value (ramped) up to max_depth.

    :param param: parameters for pony gp
    :type param: dict
    :returns: List of individuals
    :rtype: list
    """

    individuals = []
    for i in range(param["population_size"]):
        # Pick full or grow method
        full = bool(random.getrandbits(1))
        # Ramp the depth
        max_depth = (i % param["max_depth"]) + 1
        # Create root node
        symbol = get_rnd_symbol(1, max_depth, param["symbols"])
        tree = [symbol]
        # Grow the tree if the root is a function symbol
        if max_depth > 0 and symbol in param["symbols"]["functions"]:
            grow(tree, 1, max_depth, full, param["symbols"])

        # An individual is a dictionary
        individual = {
            "genome": tree,
            "fitness": DEFAULT_FITNESS
        }
        # Append the individual to the population
        individuals.append(individual)
        print('Initial tree %d: %s' % (i, tree))

    return individuals


def evaluate_fitness(individuals, param):
    """
    Perform the fitness evaluation for each individual.

    :param individuals: Population to evaluate
    :type individuals: list
    :param param: parameters for pony gp
    :type param: dict
    """
    # Iterate over all the individual solutions
    for ind in individuals:
        # Execute the fitness function
        evaluate_individual(ind, param["fitness_cases"],
                            param["targets"])


def search_loop(population, param):
    """
    Return the best individual from the evolutionary search
    loop. Starting from the initial population.

    :param population: Initial population of individuals
    :type population: list
    :param param: parameters for pony gp
    :type param: dict
    :returns: Best individual
    :rtype: Individual
    """

    # Evaluate fitness
    evaluate_fitness(population, param)
    best_ever = None

    # Generation loop
    generation = 0
    while generation < param["generations"]:
        new_population = []
        # Selection
        parents = tournament_selection(population, param)

        # Crossover
        while len(new_population) < param["population_size"]:
            # Select parents
            _parents = random.sample(parents, 2)
            # Generate children by crossing over the parents
            children = subtree_crossover(_parents[0], _parents[1], param)
            # Append the children to the new population
            for child in children:
                new_population.append(child)

        # Select population size individuals. Handles uneven population
        # sizes, since crossover returns 2 offspring
        new_population = new_population[:param["population_size"]]

        # Vary the population by mutation
        for i in range(len(new_population)):
            new_population[i] = subtree_mutation(new_population[i], param)

        # Evaluate fitness
        evaluate_fitness(new_population, param)

        # Replace population
        population = generational_replacement(new_population, population,
                                              param)
        # Print the stats of the population
        print_stats(param["generations"], population)

        # Set best solution
        sort_population(population)
        best_ever = population[0]
        # Increase the generation counter
        generation += 1

    return best_ever


def print_stats(generation, individuals):
    """
    Print the statistics for the generation and population.

    :param generation:generation number
    :type generation: int
    :param individuals: population to get statistics for
    :type individuals: list
    """

    def get_ave_and_std(values):
        """
        Return average and standard deviation.

        :param values: Values to calculate on
        :type values: list
        :returns: Average and Standard deviation of the input values
        :rtype: tuple
        """
        _ave = float(sum(values)) / len(values)
        _std = math.sqrt(float(
            sum((value - _ave) ** 2 for value in values)) / len(values))
        return _ave, _std

    # Make sure individuals are sorted
    sort_population(individuals)
    # Get the fitness values
    fitness_values = [i["fitness"] for i in individuals]
    # Get the number of nodes
    size_values = [get_number_of_nodes(i["genome"], 0) for i in individuals]
    # Get the max depth
    depth_values = [get_max_depth(i["genome"], 0, 0) for i in individuals]
    # Get average and standard deviation of fitness
    ave_fit, std_fit = get_ave_and_std(fitness_values)
    # Get average and standard deviation of size
    ave_size, std_size = get_ave_and_std(size_values)
    # Get average and standard deviation of max depth
    ave_depth, std_depth = get_ave_and_std(depth_values)
    # Print the statistics
    print(
        "Gen:%d fit_ave:%.2f+-%.3f size_ave:%.2f+-%.3f "
        "depth_ave:%.2f+-%.3f %s" %
        (generation,
         ave_fit, std_fit,
         ave_size, std_size,
         ave_depth, std_depth,
         individuals[0]))


def get_depth_from_index(node, idx, node_idx, depth, idx_depth):
    """
    Return the depth of a node based on the index. The index is based on
    depth-first left-to-right traversal

    :param node: Current node
    :type node: list
    :param idx: Current index
    :type idx: int
    :param node_idx: Index of the node which depth we are searching for
    :type node_idx: int
    :param depth: Current depth
    :type depth: int
    :param idx_depth: Depth of the node at the given index
    :type idx_depth: int
    :return: Current index and depth of the node at the given index
    :rtype: tuple
    """

    # Assign the current depth when the current index matches the given index
    if node_idx == idx:
        idx_depth = depth

    # Iterate over the children
    for child in node[1:]:
        # Increase the depth
        depth += 1
        # Recursively check the child depth and node index
        idx_depth, idx = get_depth_from_index(child, idx, node_idx, depth,
                                              idx_depth)
        # Decrease the depth
        depth -= 1

    return idx_depth, idx


def find_and_replace_subtree(root, subtree, node_idx, idx):
    """
    Returns the current index and replaces the root with another subtree at the
    given index. The index is based on depth-first left-to-right traversal.

    :param root: Root of the tree
    :type root: list
    :param subtree: Subtree that will replace the root
    :type subtree: list
    :param node_idx: Index of the node to be replaced
    :type node_idx: int
    :param idx: Current index
    :type idx: int
    :return: Current index
    :rtype: int
    """

    # Increase the index
    idx += 1

    # Check if index is a the given node
    if node_idx == idx:
        # Remove the root node
        root.pop(0)
        # Reverse the subtree
        subtree.reverse()
        # Insert the subtree at the root node
        for node in subtree:
            root.insert(0, node)

    else:
        # Iterate over the children
        for child in root[1:]:
            # Recursively travers the child
            idx = find_and_replace_subtree(child, subtree, node_idx, idx)

    return idx


def subtree_mutation(individual, param):
    """
    Return a new individual by randomly picking a node and growing a
    new subtree from it.

    :param individual: Individual to mutate
    :type individual: dict
    :param param: parameters for pony gp
    :type param: dict
    :returns: Mutated individual
    :rtype: list
    """

    # Copy the individual for mutation
    new_individual = {
        "genome": copy.deepcopy(individual["genome"]),
        "fitness": DEFAULT_FITNESS
    }
    # Check if mutation should be applied
    if random.random() < param["mutation_probability"]:
        # Pick node
        end_node_idx = get_number_of_nodes(new_individual["genome"], 0) - 1
        node_idx = random.randint(0, end_node_idx)
        node_depth, cnt = get_depth_from_index(new_individual["genome"], 0,
                                               node_idx, 0, 0)
        # Get a new symbol
        max_subtree_depth = param["max_depth"] - node_depth
        new_subtree = [get_rnd_symbol(max_subtree_depth,
                                      param["max_depth"],
                                      param["symbols"])
        ]
        # Grow tree if it was a function symbol
        if new_subtree[0] in param["symbols"]["functions"]:
            # Grow to full depth
            full = bool(random.getrandbits(1))
            # Grow subtree
            grow(new_subtree, node_depth, param["max_depth"], full,
                 param["symbols"])

        # Replace the original subtree with the new
        find_and_replace_subtree(new_individual["genome"], new_subtree,
                                 node_idx, -1)

    # Return the individual
    return new_individual


def get_nodes_with_equal_arity(root, arity, nodes, idx, arities):
    """
    Return the number of nodes and nodes with equal arity. Depth-first
    left-to-right traversal searching for nodes of a given arity

    :param root: Root of the tree
    :type root: list
    :param arity: Arity we are searching for
    :type arity: int
    :param nodes: Nodes with the given arity
    :type nodes: list
    :param idx: Current index
    :type idx: int
    :param arities: Dictionary of the symbols and their corresponding arities
    :type arities: dict
    :return: Number of nodes and nodes with a given arity
    :rtype: tuple
    """

    # Increase the current index
    idx += 1
    # Check if symbol has the given arity
    if arities[root[0]] == arity:
        # Append node to the list of symbols with equal arities
        nodes.append(root)

    # Iterate over the children
    for child in root[1:]:
        # Recursively call the child
        idx, nodes = get_nodes_with_equal_arity(child, arity, nodes, idx,
                                                arities)

    return idx, nodes


def replace_subtree(new_subtree, old_subtree):
    """
    Replace a subtree.

    :param new_subtree: The new subtree
    :type new_subtree: list
    :param old_subtree: The old subtree
    :type old_subtree: list
    """

    # Delete the nodes of the old subtree
    del old_subtree[:]
    # Reverse the new subtree
    new_subtree.reverse()
    # Iterate over the nodes
    for node in new_subtree:
        # Insert the nodes in the new subtree
        old_subtree.insert(0, copy.deepcopy(node))


def subtree_crossover(parent1, parent2, param):
    """
    Returns two individuals. The individuals are created by
    selecting two random nodes from the parents and swapping the
    subtrees.

    :param parent1: Parent one to crossover
    :type parent1: dict
    :param parent2: Parent two to crossover
    :type parent2: dict
    :param param: parameters for pony gp
    :type param: dict
    :return: Children from the crossed over parents
    :rtype: tuple
    """
    # Copy the parents to make offsprings
    offsprings = ({
                      "genome": copy.deepcopy(parent1["genome"]),
                      "fitness": DEFAULT_FITNESS
                  },
                  {
                      "genome": copy.deepcopy(parent2["genome"]),
                      "fitness": DEFAULT_FITNESS
                  })

    # Check if offspring will be crossed over
    if random.random() < param["crossover_probability"] and \
                    len(offsprings[0]["genome"]) > 1 and \
                    len(offsprings[0]["genome"]) > 0:
        # Pick a crossover point
        node_idx = random.randint(0,
                                  get_number_of_nodes(offsprings[0]["genome"],
                                                      0) - 1
        )
        offspring_0_node = get_node_at_index(offsprings[0]["genome"],
                                             node_idx)
        # Only crossover internal nodes, not only leaves
        crossover_point_symbol = offspring_0_node[0]
        if crossover_point_symbol in param["symbols"]["functions"]:
            # Get the nodes from the second offspring
            cnt, possible_nodes = \
                get_nodes_with_equal_arity(offsprings[1]["genome"],
                                           param["symbols"]["arities"][
                                               crossover_point_symbol],
                    [], -1, param["symbols"]["arities"])

            # Pick a crossover point in the second offspring
            if possible_nodes:
                # Pick the second crossover point
                offspring_1_node = random.choice(possible_nodes)
                # Swap the children of the nodes
                tmp_offspring_1_node = copy.deepcopy(offspring_1_node)
                # Copy the children from the subtree of the first offspring
                # to the chosen node of the second offspring
                replace_subtree(offspring_0_node, offspring_1_node)
                # Copy the children from the subtree of the second offspring
                # to the chosen node of the first offspring
                replace_subtree(tmp_offspring_1_node, offspring_0_node)

    # Return the offsprings
    return offsprings


def tournament_selection(population, param):
    """
    Return individuals from a population by drawing
    `tournament_size` competitors randomly and selecting the best
    of the competitors. `population_size` number of tournaments are
    held.

    :param population: Population to select from
    :type population: list
    :param param: parameters for pony gp
    :type param: dict
    :returns: selected individuals
    :rtype: list
    """

    # Iterate until there are enough tournament winners selected
    winners = []
    while len(winners) < param["population_size"]:
        # Randomly select tournament size individual solutions
        # from the population.
        competitors = random.sample(population, param["tournament_size"])
        # Rank the selected solutions
        competitors = sort_population(competitors)
        # Append the best solution to the winners
        winners.append(competitors[0])

    return winners


def generational_replacement(new_population, old_population, param):
    """
    Return new a population. The `elite_size` best old_population
    are appended to the new population. They are kept in the new
    population if they are better than the worst.

    :param new_population: the new population
    :type new_population: list
    :param old_population: the old population
    :type old_population: list
    :param param: parameters for pony gp
    :type param: dict
    :returns: the new population with the best from the old population
    :rtype: list
    """

    # Sort the population
    old_population = sort_population(old_population)
    # Append a copy of the best solutions of the old population to
    # the new population. ELITE_SIZE are taken
    for ind in old_population[:param["elite_size"]]:
        new_population.append(copy.deepcopy(ind))

    # Sort the new population
    new_population = sort_population(new_population)

    # Set the new population size
    return new_population[:param["population_size"]]


def run(param):
    """
    Return the best solution. Create an initial
    population. Perform an evolutionary search.

:param param: parameters for pony gp
    :type param: dict
    :returns: Best solution
    :rtype: dict
    """

    # Create population
    population = initialize_population(param)
    # Start evolutionary search
    best_ever = search_loop(population, param)

    return best_ever


def parse_exemplars(file_name):
    """
    Parse a CSV file. Parse the fitness case and split the data into
    Test and train data. In the fitness case file each row is an exemplar
    and each dimension is in a column. The last column is the target value of
    the exemplar.

    :param file_name: CSV file with header
    :type file_name: str
    :return: Fitness cases and targets
    :rtype: list
    """

    # Open file
    in_file = open(file_name, 'r')
    # Create a CSV file reader
    reader = csv.reader(in_file, delimiter=',')

    # Read the header
    headers = reader.next()
    print("Reading: %s headers: %s" % (file_name, headers))

    # Store fitness cases and their target values
    fitness_cases = []
    targets = []
    for row in reader:
        # Parse the columns to floats and append to fitness cases
        fitness_cases.append(map(float, row[:-1]))
        # The last column is the target
        targets.append(float(row[-1]))

    in_file.close()

    return fitness_cases, targets


def get_arities():
    """
    Return a symbol object. Helper method to keep the code clean.

    :return: Symbols used for GP individuals
    :rtype: dict
    """

    # Dictionary of symbols and their arity
    arities = {"1": 0,
               "x0": 0,
               "x1": 0,
               "+": 2,
               "-": 2,
               "*": 2,
               "/": 2,
    }
    # List of terminal symbols
    terminals = []
    # List of function symbols
    functions = []

    # Append symbols to terminals or functions by looping over the
    # arities items
    for key, value in arities.items():
        # A symbol with arity 0 is a terminal
        if value == 0:
            # Append the symbols to the terminals list
            terminals.append(key)
        else:
            # Append the symbols to the functions list
            functions.append(key)

    return {"arities": arities, "terminals": terminals, "functions": functions}


def get_test_and_train_data(fitness_cases_file, test_train_split):
    """
    Return test and train data.

    :param fitness_cases_file: CSV file with a header.
    :type fitness_cases_file: str
    :param test_train_split: Percentage of exemplar data used for training
    :type test_train_split: float
    :return: Test and train data. Both cases and targets
    :rtype: tuple
    """

    fitness_cases, targets = parse_exemplars(fitness_cases_file)
    # TODO get random cases instead of according to index
    split_idx = int(math.floor(len(fitness_cases) * test_train_split))
    training_cases = fitness_cases[:split_idx]
    test_cases = fitness_cases[split_idx:]
    training_targets = targets[:split_idx]
    test_targets = targets[split_idx:]
    return (test_cases, test_targets), (training_cases, training_targets)


def main():
    """Search. Evaluate best solution on out-of-sample data"""

    # Command line arguments
    parser = argparse.ArgumentParser()
    # Population size
    parser.add_argument("-p", "--population_size", type=int, default=20,
                        help="population size")
    # Size of an individual
    parser.add_argument("-m", "--max_depth", type=int, default=3,
                        help="Max depth of tree")
    # Number of elites, i.e. the top solution from the old population
    # transferred to the new population
    parser.add_argument("-e", "--elite_size", type=int, default=0,
                        help="elite size")
    # Generations is the number of times the EA will iterate the search loop
    parser.add_argument("-g", "--generations", type=int, default=10,
                        help="number of generations")
    # Tournament size
    parser.add_argument("-ts", "--tournament_size", type=int, default=2,
                        help="tournament size")
    # Random seed. Used to allow replication of runs of the EA. The search is
    # stochastic and and replication of the results can be guaranteed by using
    # the same random seed
    parser.add_argument("-s", "--seed", type=int, default=0,
                        help="seed number")
    # Probability of crossover
    parser.add_argument("-cp", "--crossover_probability", type=float,
                        default=1.0, help="crossover probability")
    # Probability of mutation
    parser.add_argument("-mp", "--mutation_probability", type=float,
                        default=1.0, help="mutation probability")
    # Fitness case file
    parser.add_argument("-fc", "--fitness_cases", default="",
                        help="fitness cases file")
    # Test-training data split
    parser.add_argument("-tts", "--test_train_split", type=float, default=0.7,
                        help="test-train data split")
    # Parse the command line arguments
    args = parser.parse_args()

    # Set arguments
    seed = args.seed
    test_train_split = args.test_train_split
    fitness_cases_file = 'fitness_cases.csv'  # args.fitness_cases

    test, train = get_test_and_train_data(fitness_cases_file, test_train_split)

    symbols = get_arities()

    # Print EA settings
    print(args, symbols)

    # Set random seed if not 0 is passed in as the seed
    if seed != 0:
        random.seed(seed)

    # Get the namespace dictionary
    param = vars(args)
    param["symbols"] = symbols
    param["fitness_cases"] = train[0]
    param["targets"] = train[1]
    best_ever = run(param)
    print("Best train:" + str(best_ever))
    # Test on out-of-sample data
    out_of_sample_test(best_ever, test[0], test[1])


def out_of_sample_test(individual, fitness_cases, targets):
    """
    Out-of-sample test on an individual solution

    :param individual: Solution to test on data
    :type individual: dict
    :param fitness_cases: Input data used for testing
    :type fitness_cases: list
    :param targets: Target values of data
    :type targets: list
    """
    evaluate_individual(individual, fitness_cases, targets)
    print("Best test:" + str(individual))


if __name__ == '__main__':
    main()