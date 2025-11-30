import subprocess
import sys

#Board Positions to variables

#Map a board square (row, col) to a variable number representing white queen placed
def get_white_var(row, col, board_size):
    return 1 + row * board_size + col

# Same for black queens 
def get_black_var(row, col, board_size):
    return 1 + board_size * board_size + row * board_size + col # board size^2 so offset so tehy don't overlap with whites


# Check if two squares attack each other
#Queens attack if same row, same column, or same diagonal 
def attacks(row1, col1, row2, col2):
    if row1 == row2 and col1 == col2:
        return False
    return row1 == row2 or col1 == col2 or abs(row1 - row2) == abs(col1 - col2) #boolean outcome


# Add SAT clauses ensuring that exactly army size queens are placed
# SAT encoding to control the number of true variables
#Count the number of queens placed so far with out any attack constraints 
#the squential counter do not prevent attacks themselves, just enforce exactly K queens must be placed somewhere 
def add_sequential_counter(cnf_clauses, queen_vars, army_size): #queen_vars = all squares for one color
    num_positions = len(queen_vars)
    if army_size == 0:
        for var in queen_vars:
            cnf_clauses.append([-var]) # negative literal --> variable must be False
        return
    # Set auxiliary Variables as a helper so it helps to compress encoding
    aux_offset = max(queen_vars) + 1
    count_tracker = [[aux_offset + i * army_size + j for j in range(army_size)]
                     for i in range(num_positions)]

# build a table of auxiliary variables that track how many queens picked so far 
    cnf_clauses.append([-queen_vars[0], count_tracker[0][0]])
    for j in range(1, army_size):
        cnf_clauses.append([-count_tracker[0][j]])

    # Main transitions
    for i in range(1, num_positions):
        for j in range(army_size):
            # Pass-through
            cnf_clauses.append([-count_tracker[i-1][j], count_tracker[i][j]])
            # Increment
            if j == 0:
                cnf_clauses.append([-queen_vars[i], count_tracker[i][0]])
            else:
                cnf_clauses.append([-queen_vars[i], -count_tracker[i-1][j-1], count_tracker[i][j]])

    # Enforce exactly army_size
    cnf_clauses.append([count_tracker[num_positions-1][army_size-1]])


# Build CNF for given board and army size
#
def build_cnf(board_size, army_size):
    cnf_clauses = []

    white_vars = [get_white_var(r, c, board_size) for r in range(board_size) for c in range(board_size)]
    black_vars = [get_black_var(r, c, board_size) for r in range(board_size) for c in range(board_size)]

    num_primary_vars = 2 * board_size * board_size

    # Attack constraints (
    # Same Color: Two white queens must not attack 
    # Same Color: Two black queens must not attack
    # Opposite Color: White can never attack black, black can never attack white
    for r1 in range(board_size):
        for c1 in range(board_size):
            white_var = get_white_var(r1, c1, board_size)
            black_var = get_black_var(r1, c1, board_size)
            for r2 in range(board_size):
                for c2 in range(board_size):
                    other_white_var = get_white_var(r2, c2, board_size)
                    other_black_var = get_black_var(r2, c2, board_size)
                    if attacks(r1, c1, r2, c2):
                        if white_var < other_white_var:
                            cnf_clauses.append([-white_var, -other_white_var])
                            cnf_clauses.append([-black_var, -other_black_var])
                        cnf_clauses.append([-white_var, -other_black_var])
                        cnf_clauses.append([-black_var, -other_white_var])

    # Cardinality constraints 
    #Constraint to exactly army size
    add_sequential_counter(cnf_clauses, white_vars, army_size)
    add_sequential_counter(cnf_clauses, black_vars, army_size)

    # Total variables = primary + sequential counter helpers
    total_aux_vars = 2 * len(white_vars) * army_size
    total_vars = num_primary_vars + total_aux_vars
    return total_vars, cnf_clauses


# Write CNF to DIMACS
#Got help from the sample code
# Required for input format for SAT solvers (glucose here)

def write_dimacs(filename, num_vars, cnf_clauses):
    with open(filename, "w") as f:
        f.write(f"p cnf {num_vars} {len(cnf_clauses)}\n")
        for clause in cnf_clauses:
            f.write(" ".join(map(str, clause)) + " 0\n")


# Run Glucose SAT solver
def run_glucose(cnf_file):
    solver_path = "./glucose/simp/glucose"  #The path to run the glucose can be also ./glucose if the glucose defined as executable with chmod +x
    result = subprocess.run([solver_path, cnf_file], capture_output=True, text=True)
    for line in result.stdout.splitlines():
        if "SAT" in line:
            return True
        elif "UNSAT" in line:
            return False
    return False
# If solver prints "SAT" --> return True
# If solver prints "UNSAT" --> return False



# find maximum army size
#Read board size form command line
#Compute the theoretical maximum K

def main():
    if len(sys.argv) != 2:
        print("Usage: python3 PeacableQueens.py BOARD_SIZE")
        return

    board_size = int(sys.argv[1])
    max_army = board_size * board_size // 2

    for army_size in range(max_army, 0, -1):
        print(f"Trying army size K={army_size}...")
        num_vars, cnf_clauses = build_cnf(board_size, army_size)
        write_dimacs("formula.cnf", num_vars, cnf_clauses)
        if run_glucose("formula.cnf"):
            print(f"\nMaximum number of white and black queens: {army_size}")
            return

    print("\nUNSAT — No placement possible.")

if __name__ == "__main__":
    main()

# I used a sequential counter for the cardinality constraint, and that is what cause my CNF file becomes large
