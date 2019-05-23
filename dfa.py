class DFA:
    def __init__(self):
        self.d = dict()

    def send_messasge(machine, src, dest):
        if machine not in d:
            self.d[machine] = dict()
        self.d[machine][src] = dest

    def is_valid(self, start, acceptable, sequence):
        state = start
        for s in sequence:
            state = self.d[state][s]
        return state in acceptable