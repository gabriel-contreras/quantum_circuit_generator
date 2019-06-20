from Qbit import Qbit
from qiskit import QuantumCircuit, QuantumRegister, ClassicalRegister
import math
import sys
import numpy as np


class Qgrid:

    def __init__(self, n, m, d, czfile=None, order=None,
            singlegates=True, mirror=True):
        self.n = n
        self.m = m
        self.d = d

        self.qreg = QuantumRegister(n*m, 'qreg')
        self.creg = ClassicalRegister(n*m, 'creg')
        self.circ = QuantumCircuit(self.qreg, self.creg)
        
        self.grid = self.make_grid(n,m)
        self.cz_list = self.get_CZs(n,m,fname=czfile)
        self.mirror = mirror

        if order is None:
            # Default
            self.random = False
            self.order = np.arange(len(self.cz_list))
        elif order == 'random':
            # Random order
            self.random = True
            self.order = np.arange(len(self.cz_list))
            if self.mirror is True:
                print('Order cannot be random and mirror cannot be True simultaneously. Exiting.')
                sys.exit(2)
        else:
            # Convert given order string to list of ints
            self.random = False
            self.order = [int(c) for c in order]

        self.singlegates = singlegates

    def make_grid(self,n,m):
        temp_grid = []
        index_ctr = 0
        for row in range(n):
            cur_row = []
            for col in range(m):
                cur_row += [Qbit(index_ctr,None)]
                index_ctr += 1
            temp_grid += [cur_row]

        return temp_grid

    def get_CZs(self,n,m,fname=None):
        if fname is None:
            fname = 'CZ_Layers/CZs_{}x{}.txt'.format(n,m)
        arrangements = []
        with open(fname,'r') as fn:
            for line in fn:
                if line[0] == 'A':
                    anum = int(line[1:])
                    cz_indices = []
                elif line == '\n' or line == '':
                    arrangements.append(cz_indices)
                else:
                    new_cz = line.split()
                    ctrl_str = new_cz[0].split(',')
                    ctrl = [int(g) for g in ctrl_str]
                    trgt_str = new_cz[1].split(',')
                    trgt = [int(g) for g in trgt_str]
                    cz_indices.append((ctrl,trgt))
        return arrangements

    def get_index(self, index1=None, index2=None):
        if index2 is None:
            return self.grid[index1[0]][index1[1]].index
        else:
            return self.grid[index1][index2].index

    def print_circuit(self):
        print(self.circ.draw(scale=0.6, output='text', reverse_bits=False))

    def save_circuit(self):
        str_order = [str(i) for i in self.order]
        if self.mirror:
            str_order.append('m')
        fn = 'supr_{}x{}x{}_order{}.txt'.format(self.n,self.m,self.d,"".join(str_order))
        self.circ.draw(scale=0.8, filename=fn, output='text', reverse_bits=False, 
                line_length=160)

    def initialize(self):
        for i in range(self.n):
            for j in range(self.m):
                self.circ.h(self.qreg[self.grid[i][j].h()])

    def measure(self):
        self.circ.barrier()
        for i in range(self.n):
            for j in range(self.m):
                qubit_index = self.get_index(i,j)
                self.circ.measure(self.qreg[qubit_index], self.creg[qubit_index])

    def apply_1q_gate(self, grid_loc, reserved_qubits):
        qb_index = self.get_index(grid_loc)
        if qb_index not in reserved_qubits:
            gate = self.grid[grid_loc[0]][grid_loc[1]].random_gate()
            if gate is 'T':
                # Apply a T gate to qubit at qb_index
                self.circ.t(self.qreg[qb_index])
            elif gate is 'Y':
                # Apply a sqrt-Y gate to qubit at qb_index
                self.circ.ry(math.pi/2, self.qreg[qb_index])
            elif gate is 'X':
                # Apply a sqrt-X gate to qubit at qb_index
                self.circ.rx(math.pi/2, self.qreg[qb_index])
            else:
                print('ERROR: unrecognized gate: {}'.format(gate))

    def gen_circuit(self, barriers=True):
        print('Generating {}x{}, 1+{}+1 supremacy circuit'.format(self.n,self.m,self.d))

        # Initialize with Hadamards
        self.initialize()

        # Iterate through CZ arrangements
        cz_idx = -1
        nlayer = len(self.cz_list)
        for i in range(self.d):
            prev_idx = cz_idx

            if self.mirror is True:
                if (i // nlayer) % 2 == 0:
                    cz_idx = self.order[i % nlayer]
                else:
                    cz_idx = self.order[::-1][i % nlayer]
            elif self.random is True:
                cur_mod = i % nlayer
                if cur_mod == 0:
                    random_order = np.random.permutation(self.order)
                    cz_idx = random_order[cur_mod]
                else:
                    cz_idx = random_order[cur_mod]
            else:
                cz_idx = self.order[i % nlayer]

            cur_CZs = self.cz_list[cz_idx]
            pre_CZs = self.cz_list[prev_idx]
            reserved_qubits = []

            # Apply entangling CZ gates
            for cz in cur_CZs:
                ctrl = self.get_index(cz[0])
                trgt = self.get_index(cz[1])
                reserved_qubits += [ctrl,trgt]
                self.circ.cz(self.qreg[ctrl],self.qreg[trgt])

            if i is not 0 and self.singlegates:
                # Apply single qubit gates
                for cz in pre_CZs:
                    for grid_loc in cz:
                        self.apply_1q_gate(grid_loc, reserved_qubits)

            if barriers:
                self.circ.barrier()

        # Measurement
        self.measure()

        return self.circ

    def gen_qasm(self):
        return self.circ.qasm()



