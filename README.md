# PeaceableQueens-SAT-Solver
This is a project for Propositional and Predicate Logic (NAIL062)
The provided Python Code encodes and solves the Peacable Queens problem by reducing it to SAT and calling an external SAT solver (glucose)

# Description of the Problem:
Given an n x n chessboard, we want to place:
- K white queens
- K black queens
such that no queen attack a queen of the opposite color, and queens of the same color also do not attack each other

The goal of the project is to determine the maximum possible K for a given board size n.

# SAT Encoding
Ech square (r,c) conatins:
- W(r, c) - a white queen
- B(r,c) - a black queen
  
Boolean Variables are mapped to DIMACS integers:
- White 1...n^2
- Black n^2 + 1, ... 2n^2
Total variables: 2 x n^2

# Clauses
1) At least K white queens
   - A single clause containing all white variables
   - same for black
    
2) At most K queens
   - For every (K+1)- subset of white variables:
       ¬w1 ∨ ¬w2 ∨ ... ∨ ¬w(K+1)
   - Same for black
     
3) No attacks
   - For any two squares where queens can attack each other:
     - Same Color:
       ¬W(r1,c1) ∨ ¬W(r2,c2)
       ¬B(r1,c1) ∨ ¬B(r2,c2)
     - Cross-color:
       ¬W(r1,c1) ∨ ¬W(r2,c2)
       ¬B(r1,c1) ∨ ¬B(r2,c2)
  - This enforces peace between coors and independence within wach color

# User Documentation

Main Script:

PeacableQueens.py

Usage:

python3 PeacableQueens.py <BOARD_SIZE>

- the scropt automatically searches for the maximum army size K by decreasing from ⌊n^2/2⌋ to 1.

Output

- If the solver returns SAT, the script prints:
  Maximum army size for NxN board: K = <value>
  
- If no configuration is possible:
  UNSAT — No placement possible.

# Output Files

formula.cnf — the generated DIMACS CNF (Generated a very long one because I was searching the psoibbilities sequentially)

glucose — external SAT solver (must be executable)

# Example Instances

small-sat.in: A tiny board configuartion known to be satisfiable

small-unsat.in: A configuration with no peaceful placement

# Experiments
- Small boards (n = 2-5) solve isntatnly
- Medium boards (n = 6-8) typically unders seconds depending on K
- Large board grow quickly in CNF size, performance mainly depends on K and the density of attacks 












