# check_traces.py
# Author: Caio Batista de Melo
# Date created: 2018-01-24
# Last modified: 2018-08-10
# Description: checks if a list of traces is reachable in a FSP system model;
#              can optionally draw an automata of said FSP specification.
# Requires 'graphviz' in order to export the automata. 

# TO-DO: change anytree to networkx
from anytree import Node, RenderTree
from anytree.render import AsciiStyle
from anytree.exporter.dotexporter import DotExporter
import sys

# declared globally to ease the multiple methods that use this info
states = []

class State(object):
    name = None
    transitions = None
    checked_transitions = None

    # somewhat confusing method, but it's only dealing with FSP syntax
    def __init__ (self, string):
        # switches commas(,) for / inside {} so they're not replaced further down
        flag = False
        for i in range(len(string)):
            if flag == False:
                if string[i] == "{":
                    flag = True
            else:
                if string[i] == ",":
                    string = (string[:i] + "/" + string[i+1:])
                elif string[i] == "}":
                    flag = False

        #clean up the string by removing empty spaces and commas
        string = string.replace(" ", "")
        string = string.replace("\t", "")
        string = string.replace(",", "")
        string = string.replace("(", "")
        string = string.replace(")", "")
        
        #breaks up the information
        info = string.split("=")

        self.name = info[0]
        if info[1] == 'STOP':
            self.transitions = [str("STOP->"+self.name)]
        else:
            self.transitions = info[1].split("|")
        self.checked_transitions = 0
        #print(self)

    def find_label(self, dest):
        for transition in self.transitions:
            info = transition.split("->")
            if info[1] == dest:
                return info[0]

    # this method creates a Tree (anytree) in a recursive way.
    # for each transition, an edge is added between the current state and the next one.
    def to_anytree_node (self, parent, msg):
        global states

        n = Node(self.name, parent = parent, edge = msg)

        #checks which transitions have been dealt with
        #so repeated edges don't reappear due to recursion
        while True:
            try:
                transition = self.transitions[self.checked_transitions]
                self.checked_transitions += 1
                info = transition.split("->")
                index = states.index(info[1])
                states[index].to_anytree_node(n, info[0])
            except:
                break

        return n

	# tries to find the next state given a message label
    def next_state (self, message):
        for transition in self.transitions:
            [labels, dest] = transition.split("->")
            labels = labels.replace("{", "").replace("}", "")
            for label in labels.split("/"):
                if label == message:
                    return int(float((dest[1:])))
        raise Exception("Transition not found.")


    def __str__ (self):
        ret_string = "State: " + self.name + "\n"

        ret_string += "Transitions:"
        if len(self.transitions) > 0:
            for transition in self.transitions:
                ret_string += "\n\t" + transition

        return ret_string

    def __eq__ (self, other):
        if isinstance(other, str):
            return self.name == other
        elif isinstance(other, State):
            return self.name == other.name
        else:
            return False

# this is the main method to parse the FSP spec.
def parse_fsp (filename):
    global states

    with open(filename, 'r') as myfile:
        data = myfile.read().replace('\n', ',')

    # find the starting point of the state machine. this way, there is no need to cut pieces
    # of the FSP specification out before using that as input.
    index = data.find("Q0\t=")
    data = data[index:].split(",,")


    for i, state in zip(range(len(data)), data):
        #removes the last period from the file
        #this allows for periods in messages' names
        if (i == len(data)-1):
            state = state[:-1]
        states.append(State(state))

# method defined to assis exporting anytree
def edgeattrfunc(node, child):
    global states

    index = states.index(node.name)
    s = states[index]
    msg = s.find_label(child.name)
    return str('label="'+msg+'"')

# method defined to assis exporting anytree
def edgetypefunc(node, child):
     return '->'

# this method is used to export the anytree to a PDF file.
# it requires graphviz, if it is not installed, change
# flag (export_dot) to True, so the .dot is exported instead.
def draw_anytree (filename, export_dot):
    global states

    root = states[0].to_anytree_node(None, None)

    if export_dot:
        DotExporter(root, 
        graph="digraph", 
        edgeattrfunc=edgeattrfunc,
        edgetypefunc=edgetypefunc).to_dotfile(filename+".dot")
    else:
        DotExporter(root, 
        graph="digraph", 
        edgeattrfunc=edgeattrfunc,
        edgetypefunc=edgetypefunc).to_picture(filename+".pdf")

# this method gets a list of messages that represent a trace from the test file.
# it will check if that trace is realizable from the starting state.
# in other words, this method runs a single test.
def run_test(messages):
    
    # starts at state 0
    current_state = 0
    
    try:
    	# for each message, gets the next state from the pair (current_state, current_message).
        # if no transition exists, an exception will be raised and thus this trace is not reached.
        for msg in messages:
            current_state = states[current_state].next_state(msg)
        result = "reached"
    except:
        result = "NOT reached"
    
    return result

# this method is used to run multiple tests and control the output to the user.
def prepare_tests(file):
    with open(file, 'r') as myfile:
        lines = myfile.read().split("\n")
    total_count = 0
    total_passed = 0
    local = False
    local_titles = []
    local_counts = []
    local_passeds = []

    # this is the main loop, where each test will be executed.
    for line in lines:
        if line.startswith("###"):
            if local:
                print("\n----------\n")
                local_passeds.append(local_passed)
                local_counts.append(local_count)
            print(line + "\n")
            local_titles.append(line[4:])
            local = True
            local_count = 0
            local_passed = 0
        elif line.startswith("!"):
            continue
        else: 
            line = line.replace(" ", "").replace("\t", "")
            if line == "":
                continue
            [number, test] = line.split(":")
            result = run_test(test.split(","))
            out = "    " + line + ": " + result
            print(out)
            local_count += 1
            total_count += 1
            if result == "reached":
                local_passed += 1
                total_passed += 1
    
    print("\n----------")
    print("----------\n")
    print("RESULTS SUMMARY:\n")
    if local:
        local_passeds.append(local_passed)
        local_counts.append(local_count)
        for title, count, passed in zip(local_titles, local_counts, local_passeds):
            print("%s -> traces reached: %d out of %d" % (title, passed, count))
    print("\nTotal traces reached: %d out of %d\n" % (total_passed, total_count))

def main():    
    if len(sys.argv) < 2:
        print("Error: a file should be passed as parameter!\n")
        exit(1)
    
    # parses the first file provided as a FSP specification.
    filename = sys.argv[1]
    parse_fsp(filename)

    # if the optional -DRAw flag was passed, exports the anytree to a PDF
    # if no graphviz installed, change the bool value to True so a .dot is exported.
    if "-DRAW" in sys.argv:
        draw_anytree(filename, False)
    
    # tries to run the tests inside a second file that may have been passed or not
    try:
        prepare_tests(sys.argv[2])
    except:
        pass

if __name__ == "__main__":
    main()