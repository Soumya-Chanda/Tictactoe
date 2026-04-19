"""
Tic-Tac-Toe Game Logic Engine
All game rules, win detection, and AI logic implemented here.
"""
import random
import math


# ── Win combinations ──────────────────────────────────────────────────────────
WIN_COMBOS = [
    [0, 1, 2], [3, 4, 5], [6, 7, 8],  # rows
    [0, 3, 6], [1, 4, 7], [2, 5, 8],  # cols
    [0, 4, 8], [2, 4, 6],             # diagonals
]


def check_winner(board: list) -> dict:
    """
    Check if there's a winner on the board.
    board: list of 9 elements, each 'X', 'O', or None
    Returns: {'winner': 'X'/'O'/None, 'combo': [i,j,k]/None, 'is_draw': bool}
    """
    for combo in WIN_COMBOS:
        a, b, c = combo
        if board[a] and board[a] == board[b] == board[c]:
            return {'winner': board[a], 'combo': combo, 'is_draw': False}

    if all(cell is not None for cell in board):
        return {'winner': None, 'combo': None, 'is_draw': True}

    return {'winner': None, 'combo': None, 'is_draw': False}


def get_available_moves(board: list) -> list:
    return [i for i, cell in enumerate(board) if cell is None]


def is_terminal(board: list) -> bool:
    result = check_winner(board)
    return result['winner'] is not None or result['is_draw']


# ── Minimax AI ────────────────────────────────────────────────────────────────

def minimax(board: list, depth: int, is_maximizing: bool,
            alpha: float = -math.inf, beta: float = math.inf) -> int:
    """
    Minimax algorithm with alpha-beta pruning.
    AI is 'O' (maximizing), human is 'X' (minimizing).
    """
    result = check_winner(board)
    if result['winner'] == 'O':
        return 10 - depth
    if result['winner'] == 'X':
        return depth - 10
    if result['is_draw']:
        return 0

    if is_maximizing:
        best = -math.inf
        for move in get_available_moves(board):
            board[move] = 'O'
            score = minimax(board, depth + 1, False, alpha, beta)
            board[move] = None
            best = max(best, score)
            alpha = max(alpha, best)
            if beta <= alpha:
                break
        return best
    else:
        best = math.inf
        for move in get_available_moves(board):
            board[move] = 'X'
            score = minimax(board, depth + 1, True, alpha, beta)
            board[move] = None
            best = min(best, score)
            beta = min(beta, best)
            if beta <= alpha:
                break
        return best


def get_ai_move(board: list, difficulty: str = 'medium') -> int:
    """
    Get the AI's best move based on difficulty.
    difficulty: 'easy' | 'medium' | 'hard'
    """
    available = get_available_moves(board)
    if not available:
        return -1

    if difficulty == 'easy':
        # 70% random, 30% smart
        if random.random() < 0.70:
            return random.choice(available)

    if difficulty == 'medium':
        # Check if AI can win immediately
        for move in available:
            board[move] = 'O'
            if check_winner(board)['winner'] == 'O':
                board[move] = None
                return move
            board[move] = None

        # Block human from winning
        for move in available:
            board[move] = 'X'
            if check_winner(board)['winner'] == 'X':
                board[move] = None
                return move
            board[move] = None

        # 40% random otherwise
        if random.random() < 0.40:
            return random.choice(available)

    # Hard: full minimax
    best_score = -math.inf
    best_move = available[0]
    for move in available:
        board[move] = 'O'
        score = minimax(board, 0, False)
        board[move] = None
        if score > best_score:
            best_score = score
            best_move = move

    return best_move


# ── Board utilities ───────────────────────────────────────────────────────────

def board_to_string(board: list) -> str:
    return ','.join(str(cell) if cell else 'None' for cell in board)


def string_to_board(board_str: str) -> list:
    result = []
    for cell in board_str.split(','):
        result.append(None if cell == 'None' else cell)
    return result


def new_board() -> list:
    return [None] * 9


def apply_move(board: list, position: int, symbol: str) -> list:
    """Apply a move and return updated board. Raises ValueError if invalid."""
    if position < 0 or position > 8:
        raise ValueError(f"Invalid position: {position}")
    if board[position] is not None:
        raise ValueError(f"Position {position} already occupied")
    board = board.copy()
    board[position] = symbol
    return board


def get_board_display(board: list) -> str:
    """Return ASCII representation of the board for debugging."""
    symbols = [cell if cell else str(i) for i, cell in enumerate(board)]
    return (
        f" {symbols[0]} | {symbols[1]} | {symbols[2]} \n"
        f"---+---+---\n"
        f" {symbols[3]} | {symbols[4]} | {symbols[5]} \n"
        f"---+---+---\n"
        f" {symbols[6]} | {symbols[7]} | {symbols[8]} \n"
    )
