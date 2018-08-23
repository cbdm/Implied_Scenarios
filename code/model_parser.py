# model_parser.py
# Author: Caio Batista de Melo
# Date Created: 2018-05-03
# Last Modified: 2018-08-08
# Description: Parses an easier to understand model into LTSA's xml.
# New Addition (2018-05-09): can export expected behaviors to be included in the test file.
# New Addition (2018-08-08): can export more expected behaviors to be included in the test file with the export_expected_behaviors method.
#                            The original one (simple_expected_behaviors) was also kept to preserve the original functionality, if wanted it 
#                            can also be used as it is simpler to understand.


import re
import sys
import networkx as nx

# declared globally so error messages are better explained
line_number = None

class Indentation (): # class used to indent the XML
    indent = ''
    # Indentation size
    size = 2

    def increase ():
        for _ in range(Indentation.size):
            Indentation.indent += ' '

    def decrease ():
        try:
            Indentation.indent = Indentation.Indent[Indentation.size:]
        except:
            Indentation.indent = ''

class Transition (object): # stores a transition between bmscs
    To = None
    From = None

    def __init__ (self, From, To):
        self.To = To
        self.From = From

    def __str__ (self):
        return self.From + "->" + self.To

class Message (object): # holds information of a single message
    To = None
    From = None
    msg = None
    time = None

    def __init__ (self, From, To, msg, time):
        self.To = To
        self.From = From
        self.msg = msg
        self.time = time

    def __eq__ (self, other):
        if other == None:
            return False
        else:
            return self.msg == other.msg and self.To == other.To and self.From == other.From and self.time == other.time

    def __str__ (self):
        return self.From.lower() + "." + self.To.lower() + "." + self.msg

class Instance (object): # holds information of an instance inside a single scenario
    name = None
    output = None
    Input = None

    def __init__ (self, name):
        self.name = name
        self.output = []
        self.Input = []

    def add_out (self, msg):
        self.output.append(msg)

    def add_in (self, msg):
        self.Input.append(msg)

    def add_message (self, msg):
        ret = 0
        if msg.To == self.name:
            self.add_in(msg)
            ret += 1
        if msg.From == self.name:
            self.add_out(msg)
            ret += 1
        return ret

class Scenario (object):
    name = None
    instances = None
    empty = None

    def __init__ (self, name, instance_names):
        self.name = name
        self.instances = []
        self.empty = True
        for instance_name in instance_names:
            self.instances.append(Instance(instance_name))

    # goes through instances trying to add the message
    # returns how many times the message has been added
    def add_message (self, message):
        found = 0
        for inst in self.instances:
            found += inst.add_message(message)
        if found > 0:
            self.empty = False
        return found

    def get_ordered_messages (self):
        total_count = 0
        
        for instance in self.instances:
            total_count += len(instance.output)

        messages = []
        last_timeindex = 0

        while len(messages) < total_count:
            next_timeindex = last_timeindex + 1000
            instance_index = 0
            message_index = 0
            last_message_added = None

            for i, instance in zip(range(len(self.instances)), self.instances):
                for j, message in zip(range(len(instance.output)), instance.output):
                    if message.time <= next_timeindex and message.time >= last_timeindex:
                        # this condition allows us to have two messages with the same timeindex
                        if message.time == last_timeindex:
                            found = False
                            for k in range(len(messages)-1, -1, -1):
                                if messages[k] == message:
                                    found = True
                                    break

                            if found:
                                continue

                        next_timeindex = message.time
                        instance_index = i
                        message_index = j

            messages.append(self.instances[instance_index].output[message_index])
            last_timeindex = next_timeindex

        return messages


    def __eq__ (self, string):
        return self.name == string

class Model (object):
    instances = None
    transitions = None
    scenarios = None
    scenario_titles = None
    title = None
    timeindex = None

    def __init__ (self, title):
        self.title = title
        self.instances = []
        self.transitions = []
        self.scenarios = []
        self.scenario_titles = []

    def add_transition (self, transition):
        info = transition.split('->')

        # checks if scenarios have already been encountered
        if info[0] not in self.scenario_titles:
            self.scenario_titles.append(info[0])
        if info[1] not in self.scenario_titles:
            self.scenario_titles.append(info[1])

        # adds the new transition
        self.transitions.append(Transition(info[0], info[1]))

    def add_instance (self, instance):
        self.instances.append(instance)

    def add_scenario (self, scenario_title):
        self.scenarios.append(Scenario(scenario_title, self.instances))
        # restarts the timeindex for current scenario
        self.timeindex = 1

    def add_message (self, message):
        global line_number
        
        try:
            insts, msg = message.split(':')
            From, To = insts.split('->')
            
            # checks if the message isn't to itself
            if From == To:
                print("ERROR (line %d): LTSA doesn't allow a component to send itself a message." % line_number)
                print("Hint: you could create an auxiliary instance to go around this.")
                return

            # a '&' in the end of a message indicates that timeindex
            # shouldn't be increased for the next message
            if (msg[-1] == '&'):
                m = Message(From, To, msg[:-1], self.timeindex)
            else:
                m = Message(From, To, msg, self.timeindex)
                # increases the timeindex for next message
                self.timeindex += 1
            
            # adds the message and tests if both instances are known
            if self.scenarios[-1].add_message(m) < 2:
                print("ERROR (line %d): unknown instance on message." % line_number)
        except ValueError:
            print("ERROR (line %d): badly formatted message." % line_number)
        except IndexError:
            print("ERROR (line %d): a scenario should be created before a message." % line_number)
        except TypeError:
            print("ERROR (line %d): a scenario should be created before a message." % line_number)

    def generate (self):
        # headers of the xml

        xml = Indentation.indent + '<?xml version="1.0" encoding="UTF-8"?>\n'
        xml += Indentation.indent + '<specification>\n'

        Indentation.increase()

        # hmsc part

        xml += Indentation.indent + '<hmsc>\n\n'

        Indentation.increase()

        init_x = 50
        init_y = 30

        step_x = 120
        step_y = 100

        pos_x = 50
        pos_y = init_y - step_y

        # first the bmscs are added

        if 'init' not in self.scenario_titles:
            self.scenario_titles = ['init'] + self.scenario_titles
        len_x = int(round(len(self.scenario_titles) ** .5 + .5)) # +.5 just to round up

        for i, inst in zip(range(len(self.scenario_titles)), self.scenario_titles):
            if i % len_x == 0:
                pos_x = init_x
                pos_y += step_y
            
            xml += Indentation.indent + '<bmsc name="' + inst + '" x="' + str(pos_x) + '" y="' + str(pos_y) + '"/>\n'
            
            pos_x += step_x


        xml += '\n'

        # now we add the transitions

        for transition in self.transitions:
            xml += Indentation.indent + '<transition>\n'
            Indentation.increase()

            xml += Indentation.indent + '<from>' + transition.From + '</from>\n'
            xml += Indentation.indent + '<to>' + transition.To + '</to>\n'

            Indentation.decrease()
            xml += Indentation.indent + '</transition>\n\n'


        Indentation.decrease()

        xml += Indentation.indent + '</hmsc>\n\n'

        # end of hmsc part

        # now the bmscs are added
        # fist empty scenarios that only show up in hmsc
        for scenario in self.scenario_titles:
            if scenario not in self.scenarios:
                xml += Indentation.indent + '<bmsc name="' + scenario + '" />\n\n'

        # now we add the model's scenarios that actually have things
        for scenario in self.scenarios:
            # checks if it's an empty scenario
            if scenario.empty:

                xml += Indentation.indent + '<bmsc name="' + scenario.name + '" />\n\n'

            else:

                xml += Indentation.indent + '<bmsc name="' + scenario.name + '">\n'

                Indentation.increase()

                for instance in scenario.instances:
                    # checks if it's an empty instance
                    if (len(instance.output) + len(instance.Input)) == 0:
                        
                        xml += Indentation.indent + '<instance name="' + instance.name + '" />\n'

                    else:
                        # starts this instance
                        xml += Indentation.indent + '<instance name="' + instance.name + '">\n'
                        Indentation.increase()

                        # first write the outgoing messages
                        for message in instance.output:
                            xml += Indentation.indent + '<output timeindex="' + str(message.time) + '">\n'
                            Indentation.increase()

                            xml += Indentation.indent + '<name>' + message.From.lower() + ',' + message.To.lower() + ',' + message.msg + '</name>\n'
                            xml += Indentation.indent + '<to>' + message.To + '</to>\n'
                            
                            Indentation.decrease()
                            xml += Indentation.indent + '</output>\n'
                        

                        # then the incoming messages
                        for message in instance.Input:
                            xml += Indentation.indent + '<input timeindex="' + str(message.time) + '">\n'
                            Indentation.increase()


                            xml += Indentation.indent + '<name>' + message.From.lower() + ',' + message.To.lower() + ',' + message.msg + '</name>\n'
                            xml += Indentation.indent + '<from>' + message.From + '</from>\n'

                            Indentation.decrease()
                            xml += Indentation.indent + '</input>\n'

                        # end of this instance
                        Indentation.decrease()
                        xml += Indentation.indent + '</instance>\n'
                        

                Indentation.decrease()

                xml += Indentation.indent + '</bmsc>\n\n'


        # lastly, we close the specification tag
        Indentation.decrease()
        xml += Indentation.indent + '</specification>'

        try:
            with open(self.title + '.xml', 'w') as file_out:
                file_out.write(xml)
        except:
            print("ERROR: unable to create file: '" + self.title + ".xml'.")

    # exports the expected behaviors to be included in the test file
    # this method exports the sequences of scenarios that start from
    # the initial node and ends either in the original node again, or
    # in a terminal node. It also removes loops.
    def simple_expected_behaviors(self):
        G = nx.DiGraph()

        G.add_nodes_from(self.scenario_titles)

        for transition in self.transitions:
            G.add_edge(transition.From, transition.To)

        if len(list(G.predecessors('init'))) > 0 or len(list(G.successors('init'))) > 1:
            root = 'init'
        else:
            root = list(G.successors('init'))[0]

        paths = []
        restarting_nodes = list(G.predecessors(root))
        
        # first we add the paths that come back to the inicial scenario
        for node in restarting_nodes:
            current_paths = list(nx.all_simple_paths(G, root, node))
            for path in current_paths:
                # includes the start state so we know the system can execute again
                paths.append(path + [root])

        # now we add the paths that start on the intiial and end on a terminal node
        for node in G.nodes:
            if len(list(G.successors(node))) == 0:
                paths += list(nx.all_simple_paths(G, root, node))

        try:
            filename = self.title + '_expected_behaviors.txt'
            with open(filename, 'w') as file_out:
                out = '### Expected Behaviors\n\n'
                for i, path in zip(range(len(paths)), paths):
                    out += "! "
                    for scenario in path:
                        out += scenario + ', '
                    try:
                        out = out[:-2] + '\n'
                    except:
                        pass
                    out += str(i) + ": "

                    for scenario in path:
                        try:
                            index = self.scenarios.index(scenario)
                        except:
                            continue
                        messages = self.scenarios[index].get_ordered_messages()
                        
                        for msg in messages:
                            out += str(msg) + ', '

                    out = out[:-2] +  "\n\n"

                file_out.write(out)
        except:
            print("ERROR: unable to create file: '" + filename + "'.")

    # exports the expected behaviors to be included in the test file
    # this method exports more scenarios than the original one above;
    # it exports paths that start in the root node and are not prefixes
    # of other paths (i.e., maximal paths). It also includes one iteration
    # of the loops that are of two scenarios (e.g., s1->s2->s1).
    def export_expected_behaviors(self):
        # creates a directed graph which will serve as the hMSC
        G = nx.DiGraph()
        # adds the scenarios (bMSCs) as the nodes
        G.add_nodes_from(self.scenario_titles)
        # adds the transitions between scenarios as edges
        for transition in self.transitions:
            G.add_edge(transition.From, transition.To)

        root = 'init' # sets the current scenario as init (initial scenario in LTSA-MSC)
        paths = [[root]] # will contains all expected sequences of scenarios
        visited = [root] # list that contains the already visited scenarios, used to prevend infinite loops
        to_go = list(G.successors(root)) # nodes that still need to be visited
        previous_future_nodes = [(root,node) for node in list(G.predecessors(root)) if node in to_go] # contains the nodes that are both predecessors and successors of the current node

        # loops while there are nodes to be visited
        while len(to_go) > 0:
            # visits the next node and removes it from the ones to go
            current = to_go.pop(0)
            # adds the current node to the list of visited ones
            visited.append(current)

            # gets the previous nodes that can reach the current one
            previous_nodes = list(G.predecessors(current))
            # gets the nodes that can be reached from this one
            future_nodes = list(G.successors(current))

            # adds the new nodes reachable from this one to the next nodes to be visited
            for node in future_nodes:
                # checks if the node is not already in the list nor has it been already visited
                if node not in to_go and node not in visited:
                    to_go.append(node)

                # checks if this is a node that both reaches current and is reached by current
                if node in previous_nodes and node != current and (node, current) not in previous_future_nodes:
                    previous_future_nodes.append((current, node))

            # gets all paths that can get here from the root node and adds them to the list of paths
            new_paths = list(nx.all_simple_paths(G, root, current))            
            paths += new_paths

        # now it adds the transitions that goes to a node and comes back to the same one
        # therefore, loops all pairs that were added as previous and future nodes

        new_paths = [] # stores the new created paths for this first loop insertion

        for i, (node1, node2) in enumerate(previous_future_nodes):
            # goes through the original paths to make the new inclusions
            for path in paths:

                # finds all positions that node1 occurs in path
                positions1 = [index for index,scenario in enumerate(path) if scenario == node1]
                # finds all positions that node1 occurs in path
                positions2 = [index for index,scenario in enumerate(path) if scenario == node2]

                # finds the positions where node1 occurs in path and it is not proceeded by node2, so we do not add repeated loops
                positions = [pos for pos in positions1 if (pos+1) not in positions2]
                
                # loops 2^n times to allow all possibilities of changes in the positions
                for k in range(2**len(positions)):
                    # makes a copy in memory to not mess up the original path
                    new_path = path.copy()
                    # used to keep the index correct when the new messages are added
                    changes = 0

                    # checks if each position should be replaced or not
                    for j in range(len(positions)):
                        # checks if the bit for the current position is to be fixed (1) or not (0)
                        if 2**j & k:
                            # if the insertion is needed, then keep the same scenarios before and after, and add the expansion in the position
                            new_path = new_path[:positions[j]+changes] + [node1, node2] + new_path[positions[j]+changes:]
                            changes += 1

                    new_paths.append(new_path) # adds the new path to the list of new paths
        
        # finally adds the new paths created
        # notice that only two levels of loops are created, however we could go further with this process if desired
        paths += new_paths
        

        # removes paths that are prefixes of other paths, that is,
        # paths that are subpaths for other paths also included
        # to achieve this, we add the unique paths that are not prefix of other paths in the new list
        unique_paths = []

        for p1 in paths:
            
            # checks if p1 is already inserted
            if p1 not in unique_paths:
                unique_paths.append(p1)
            else:
                continue

            # converts the sequence of scenarios to a string containing only letters and numbers
            # this is done to allow the use of the 'startswith' method of the string class
            s1 = re.sub(r"[^A-Za-z0-9]+", '', str(p1))
            
            for p2 in paths:
                
                # checks if the elements are equal and if p2 is further down in the list, so we keep the first appearence of the path
                if p1 == p2:
                    continue
        
                # converts the sequence of scenarios to a string containing only letters and numbers
                s2 = re.sub(r"[^A-Za-z0-9]+", '', str(p2))

                # if p1 is a prefix to another path, remove p1 from the unique paths and breaks the inner loop
                if s2.startswith(s1):
                    unique_paths.remove(p1)
                    break

        try:
            filename = self.title + '_expected_behaviors.txt'
            with open(filename, 'w') as file_out:
                out = '### Expected Behaviors\n\n'
                for i, path in zip(range(len(unique_paths)), unique_paths):
                    out += "! "
                    for scenario in path:
                        out += scenario + ', '
                    try:
                        out = out[:-2] + '\n'
                    except:
                        pass
                    out += str(i) + ": "

                    for scenario in path:
                        try:
                            index = self.scenarios.index(scenario)
                        except:
                            continue
                        messages = self.scenarios[index].get_ordered_messages()
                        
                        for msg in messages:
                            out += str(msg) + ', '

                    out = out[:-2] +  "\n\n"

                file_out.write(out)
        except:
            print("ERROR: unable to create file: '" + filename + "'.")

    # exports a list with all messages of this model
    def export_all_messages (self):
        all_messages = []

        for scenario in self.scenarios:
            messages = scenario.get_ordered_messages()

            for message in messages:
                msg = str(message)
                if msg not in all_messages:
                    all_messages.append(msg)

        try:
            filename = self.title + '_all_messages.txt'
            with open(filename, 'w') as file_out:
                out = ''
                for msg in all_messages:
                    out += msg + '\n'
                file_out.write(out)
        except:
            print("ERROR: unable to create file: '" + filename + "'.")

def parse_model (filename):
    try:
        with open(filename, 'r') as file_in:
            lines = file_in.read().split('\n')
    except:
        print("ERROR: unable to open file: '" + filename + "'.")
        return

    model = None

    try:
        global line_number
        for line_number, line in zip(range(1,len(lines)+1), lines):
            # not done before so the error shows on the correct line
            line = line.replace(' ', '').replace('\t', '')

            if line.startswith('//') or line == '': # ignore comments and blank lines
            
                continue
            
            elif line.startswith('!'): # title line
            
                if model != None:
            
                    print("ERROR (line %d): title has already been defined." % line_number)
            
                model = Model(line[1:])
            
            elif line.startswith('@'): # transitions between scenarios

                model.add_transition(line[1:])
            
            elif line.startswith('#'): # instances
            
                model.add_instance(line[1:])
            
            elif line.startswith('$'): # scenarios
                
                if line == '$init':
                    print("ERROR (line %d): 'init' is a reserved scenario in LTSA." % line_number)
                else:
                    model.add_scenario(line[1:])
            
            elif line.startswith('%'): # messages
            
                model.add_message(line[1:])
            
            else:
            
                print("ERROR (line %d): unexpected syntax." % line_number)

    except AttributeError:
        print("ERROR: title hasn't been defined yet.")

    return model

if __name__ == "__main__":
    try:
        model = parse_model(sys.argv[1])
        model.generate()

        if "-t" in sys.argv or "-T" in sys.argv:
            model.export_expected_behaviors()
            
            # the following line of code can be uncommented to export a file
            # that contains all messages in the specification. It's useful
            # for creating constraints in the lts (LTSA architecture) model. 
            
            # model.export_all_messages()
        else:
            print("HINT: you can export positive scenarios with '-t'.")

    except IndexError:
        print("ERROR: a file should be passes as argument.")