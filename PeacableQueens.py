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

# For this part of the code (add_sequential_counter) I got some help from existing sources and found out that SAT solvers only understand boolean variables, 
# so you cannot directly say “exactly 3 queens” which my problem specificly asks for this 

# Add SAT clauses ensuring that exactly army size queens are placed
# SAT encoding to control the number of true variables
#Count the number of queens placed so far with out any attack constraints 
#the squential counter do not prevent attacks themselves, just enforce exactly K queens must be placed somewhere 
#But it does help us to forbid the impossible states and builds the possible transition for cnf
def add_sequential_counter(cnf_clauses, queen_vars, army_size): #queen_vars = all squares for one color
    num_positions = len(queen_vars)
    # Special Case: If we want exactly 0 queens, we need to force all variables to be false
    if army_size == 0:
        for var in queen_vars:
            cnf_clauses.append([-var]) # negative literal --> variable must be False
        return
    # Set auxiliary Variables as a helper so it helps to compress encoding
    #Variables start After the largest queen variable (its like if we have 10 queens our variables start from 41)
    aux_offset = max(queen_vars) + 1
    count_tracker = [[aux_offset + i * army_size + j for j in range(army_size)] # check how many queens so far
                     for i in range(num_positions)]
# By this we did the following:
# build a table of auxiliary variables that track how many queens picked so far 
# Here count_tracker[i][j] stands for "after scanning squares 0...i, we can potentially reach the state j
    #count_tracker[i][j] = True if it is possible to have counted (j+1) queens up to position i
    # i = square index that we have in our board
    # j = count state (0 = 1 queen, 1 = 2 queens (beacuse index starts from 0))

    # if we have n=4 size chessboard we would have 16 variables for white queens (16 squares)
    # The code trys possible K values in ascending order. For example if we had K = 3 The logic checks as follows:
    # count_traker[i][j] where i = 0...15 (board squares), j = 0..2 (0=1 queen, 1=2 queens, 2=3 queens) so we would have 48 auxiliary variables

    #Now we do the initialization step for i = 0
    cnf_clauses.append([-queen_vars[0], count_tracker[0][0]]) #initialization we check square 0 Q(0) if Q[0] = 1 (there is a queen) then count = 1 
    #Clause: (¬Q0 v count_tracker[0][0]) --> (If Q0 = True then count_tracker[0][0] must be True, If Q0 = False then clause is already satisfied)
    # All higher counts are impossile at i = 0 
    
    #Clause: ¬count_tracker[0][j] This is beacuse at square 0, you cannot hace 2 or more queens (you have 1 square not enough space to fit more)
    for j in range(1, army_size):
        cnf_clauses.append([-count_tracker[0][j]])
  
    # Main transitions
    for i in range(1, num_positions):
        for j in range(army_size):
            # Pass-through
            #Clause (¬count_tracker[i-1][j] v count_tracker[i][j])
            #If we already had >= j+1 queens at square i-1 we must keep that true at square i
            cnf_clauses.append([-count_tracker[i-1][j], count_tracker[i][j]])
            # Increment
            #If the current square has a queen, increase the count
            if j == 0:
                #If square i has a queen, we certainly have >= 1 queen now 
                #Clause: (¬Qi v count_tracker[i][0])
                cnf_clauses.append([-queen_vars[i], count_tracker[i][0]])
            else:
                #for j >= 1:
                #Clause: (¬Qi v ¬count_tracker[i-1][j-1] v count_tracker[i][j])
                #If Qi = True and previously we had >= j queens, then now we must have >= j+1 queens 
                cnf_clauses.append([-queen_vars[i], -count_tracker[i-1][j-1], count_tracker[i][j]])

    # Enforce exactly army_size
    #count_tracker[num_positions-1][army_size-1] must be true
    #After the last square the unary counter must give at least K queens, exactly k, because all higher levels are impossible to construct
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

    # This part picks square (r1, c1)
    # We compute white_var = variable number for white queen on that square and black_var = same for black queens 
    for r1 in range(board_size):
        for c1 in range(board_size):
            white_var = get_white_var(r1, c1, board_size)
            black_var = get_black_var(r1, c1, board_size)

            #This picks up square (r2, c2) and computes their variable ID's
            for r2 in range(board_size):
                for c2 in range(board_size):
                    other_white_var = get_white_var(r2, c2, board_size)
                    other_black_var = get_black_var(r2, c2, board_size)

                    #If two squares are in the same row, column or diagonal then the queens would attack each other
                    if attacks(r1, c1, r2, c2):
                        if white_var < other_white_var: #This is for adding same color attack clauses once (no override)
                            #If square A attacks B: Pair (A,B) should be added Pair (B,A) must not be added Again 
                            cnf_clauses.append([-white_var, -other_white_var]) #No two white queens attack each other
                            cnf_clauses.append([-black_var, -other_black_var]) #No two black queens attack each other
                        #Opposite colors cannot attack each other
                        cnf_clauses.append([-white_var, -other_black_var]) # white on A and white on B 
                        cnf_clauses.append([-black_var, -other_white_var]) # black on A and white on B 

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
