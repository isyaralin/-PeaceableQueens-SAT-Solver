import subprocess
import sys

# -----------------------------------------------------------
# Map board positions to SAT variables
# -----------------------------------------------------------
def get_white_var(row, col, board_size):
    return 1 + row * board_size + col

def get_black_var(row, col, board_size):
    return 1 + board_size * board_size + row * board_size + col

# -----------------------------------------------------------
# Check if two squares attack each other
# -----------------------------------------------------------
def attacks(row1, col1, row2, col2):
    if row1 == row2 and col1 == col2:
        return False
    return row1 == row2 or col1 == col2 or abs(row1 - row2) == abs(col1 - col2)

# -----------------------------------------------------------
# Sequential counter for exactly army_size queens
# -----------------------------------------------------------
def add_sequential_counter(cnf_clauses, queen_vars, army_size):
    num_positions = len(queen_vars)
    if army_size == 0:
        for var in queen_vars:
            cnf_clauses.append([-var])
        return

    aux_offset = max(queen_vars) + 1
    count_tracker = [[aux_offset + i * army_size + j for j in range(army_size)]
                     for i in range(num_positions)]

    # Initialize first position
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

# -----------------------------------------------------------
# Build CNF for given board and army size
# -----------------------------------------------------------
def build_cnf(board_size, army_size):
    cnf_clauses = []

    white_vars = [get_white_var(r, c, board_size) for r in range(board_size) for c in range(board_size)]
    black_vars = [get_black_var(r, c, board_size) for r in range(board_size) for c in range(board_size)]

    num_primary_vars = 2 * board_size * board_size

    # Attack constraints (no two queens attack same-color or opposite-color)
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

    # Cardinality constraints (exactly army_size)
    add_sequential_counter(cnf_clauses, white_vars, army_size)
    add_sequential_counter(cnf_clauses, black_vars, army_size)

    # Total variables = primary + sequential counter helpers
    total_aux_vars = 2 * len(white_vars) * army_size
    total_vars = num_primary_vars + total_aux_vars
    return total_vars, cnf_clauses

# -----------------------------------------------------------
# Write CNF to DIMACS
# -----------------------------------------------------------
def write_dimacs(filename, num_vars, cnf_clauses):
    with open(filename, "w") as f:
        f.write(f"p cnf {num_vars} {len(cnf_clauses)}\n")
        for clause in cnf_clauses:
            f.write(" ".join(map(str, clause)) + " 0\n")

# -----------------------------------------------------------
# Run Glucose SAT solver
# -----------------------------------------------------------
def run_glucose(cnf_file):
    solver_path = "./glucose/simp/glucose"  # adjust path if needed
    result = subprocess.run([solver_path, cnf_file], capture_output=True, text=True)
    for line in result.stdout.splitlines():
        if "SAT" in line:
            return True
        elif "UNSAT" in line:
            return False
    return False

# -----------------------------------------------------------
# Main: find maximum army size
# -----------------------------------------------------------
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
