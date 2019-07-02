# quantum-circuit-generator
Python package for automated generation of quantum dynamics and supremacy circuits

## Getting Started

### Prerequisites

Install the qiskit python package via pip.

```
pip install qiskit
```

### Generation Example
To generate circuits using the scripts in this package, first place the entire quantum_circuit_generator directory in your project like so

```
your_project_folder/
    your.py
    files.py
    here.py
    quantum_circuit_generator/
```

As an example, you can generate a 4x4x8 supremacy circuit with the following lines

```
from quantum_circuit_generator.gen_supremacy import generate

circ = generate(4,4,8)
print(circ)
```
