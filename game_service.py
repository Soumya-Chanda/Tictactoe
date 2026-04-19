"""
Game Service: Database operations for games, moves, stats, and analytics.
"""
from database.models import get_db
from datetime import datetime, timezone


# ── Game CRUD ─────────────────────────────────────────────────────────────────

def create_game(player1_id: int, game_mode: str,
                player2_id: int = None, ai_difficulty: str = 'medium') -> int:
    """Create a new game and return its ID."""
    conn = get_db()
    c = conn.cursor()
    try:
        c.execute('''
            INSERT INTO games (player1_id, player2_id, game_mode, ai_difficulty, board_state)
            VALUES (?, ?, ?, ?, ?)
        ''', (player1_id, player2_id, game_mode, ai_difficulty,
              'None,None,None,None,None,None,None,None,None'))
        game_id = c.lastrowid
        conn.commit()
        return game_id
    finally:
        conn.close()


def record_move(game_id: int, player_id: int | None, position: int,
                symbol: str, move_number: int, board_state: str):
    """Record a move in the database."""
    conn = get_db()
    c = conn.cursor()
    try:
        c.execute('''
            INSERT INTO moves (game_id, player_id, position, symbol, move_number)
            VALUES (?, ?, ?, ?, ?)
        ''', (game_id, player_id, position, symbol, move_number))
        c.execute('UPDATE games SET board_state = ?, moves_count = ? WHERE id = ?',
                  (board_state, move_number, game_id))
        conn.commit()
    finally:
        conn.close()


def end_game(game_id: int, winner_id: int | None, is_draw: bool,
             duration_seconds: int):
    """Mark a game as finished."""
    conn = get_db()
    c = conn.cursor()
    try:
        c.execute('''
            UPDATE games
            SET winner_id = ?, is_draw = ?, duration_seconds = ?, ended_at = CURRENT_TIMESTAMP
            WHERE id = ?
        ''', (winner_id, 1 if is_draw else 0, duration_seconds, game_id))
        conn.commit()
    finally:
        conn.close()


def update_player_stats(user_id: int, result: str, game_mode: str,
                        moves_count: int, won: bool):
    """
    Update player_stats after a game.
    result: 'win' | 'loss' | 'draw'
    game_mode: 'pvp' | 'pvc'
    """
    conn = get_db()
    c = conn.cursor()
    try:
        c.execute('SELECT * FROM player_stats WHERE user_id = ?', (user_id,))
        row = c.fetchone()
        if not row:
            c.execute('INSERT INTO player_stats (user_id) VALUES (?)', (user_id,))
            conn.commit()
            c.execute('SELECT * FROM player_stats WHERE user_id = ?', (user_id,))
            row = c.fetchone()

        stats = dict(row)
        stats['total_games'] += 1
        stats['total_moves'] += moves_count

        if result == 'win':
            stats['wins'] += 1
            stats['win_streak'] += 1
            stats['max_win_streak'] = max(stats['max_win_streak'], stats['win_streak'])
            if moves_count < stats['fastest_win_moves']:
                stats['fastest_win_moves'] = moves_count
            if game_mode == 'pvp':
                stats['pvp_wins'] += 1
            else:
                stats['pvc_wins'] += 1
        elif result == 'loss':
            stats['losses'] += 1
            stats['win_streak'] = 0
            if game_mode == 'pvp':
                stats['pvp_losses'] += 1
            else:
                stats['pvc_losses'] += 1
        else:  # draw
            stats['draws'] += 1
            stats['win_streak'] = 0
            if game_mode == 'pvp':
                stats['pvp_draws'] += 1
            else:
                stats['pvc_draws'] += 1

        c.execute('''
            UPDATE player_stats SET
                total_games=?, wins=?, losses=?, draws=?,
                pvp_wins=?, pvp_losses=?, pvp_draws=?,
                pvc_wins=?, pvc_losses=?, pvc_draws=?,
                win_streak=?, max_win_streak=?,
                total_moves=?, fastest_win_moves=?,
                updated_at=CURRENT_TIMESTAMP
            WHERE user_id=?
        ''', (
            stats['total_games'], stats['wins'], stats['losses'], stats['draws'],
            stats['pvp_wins'], stats['pvp_losses'], stats['pvp_draws'],
            stats['pvc_wins'], stats['pvc_losses'], stats['pvc_draws'],
            stats['win_streak'], stats['max_win_streak'],
            stats['total_moves'], stats['fastest_win_moves'],
            user_id
        ))
        conn.commit()
    finally:
        conn.close()


def get_game(game_id: int) -> dict | None:
    conn = get_db()
    c = conn.cursor()
    try:
        c.execute('SELECT * FROM games WHERE id = ?', (game_id,))
        row = c.fetchone()
        return dict(row) if row else None
    finally:
        conn.close()


# ── Analytics ─────────────────────────────────────────────────────────────────

def get_player_stats(user_id: int) -> dict:
    conn = get_db()
    c = conn.cursor()
    try:
        c.execute('SELECT * FROM player_stats WHERE user_id = ?', (user_id,))
        row = c.fetchone()
        if not row:
            return {}
        stats = dict(row)
        total = stats['total_games']
        stats['win_rate'] = round(stats['wins'] / total * 100, 1) if total else 0
        return stats
    finally:
        conn.close()


def get_recent_games(user_id: int, limit: int = 10) -> list:
    conn = get_db()
    c = conn.cursor()
    try:
        c.execute('''
            SELECT g.*, 
                   u1.username as player1_name, u1.avatar_color as p1_color,
                   u2.username as player2_name, u2.avatar_color as p2_color,
                   w.username as winner_name
            FROM games g
            LEFT JOIN users u1 ON g.player1_id = u1.id
            LEFT JOIN users u2 ON g.player2_id = u2.id
            LEFT JOIN users w ON g.winner_id = w.id
            WHERE g.player1_id = ? OR g.player2_id = ?
            ORDER BY g.created_at DESC
            LIMIT ?
        ''', (user_id, user_id, limit))
        rows = c.fetchall()
        return [dict(r) for r in rows]
    finally:
        conn.close()


def get_win_loss_over_time(user_id: int) -> dict:
    """Get wins/losses grouped by date for line chart."""
    conn = get_db()
    c = conn.cursor()
    try:
        c.execute('''
            SELECT 
                DATE(ended_at) as date,
                SUM(CASE WHEN winner_id = ? THEN 1 ELSE 0 END) as wins,
                SUM(CASE WHEN winner_id != ? AND is_draw = 0 
                         AND (player1_id = ? OR player2_id = ?) 
                         AND ended_at IS NOT NULL THEN 1 ELSE 0 END) as losses,
                SUM(CASE WHEN is_draw = 1 THEN 1 ELSE 0 END) as draws
            FROM games
            WHERE (player1_id = ? OR player2_id = ?) AND ended_at IS NOT NULL
            GROUP BY DATE(ended_at)
            ORDER BY date DESC
            LIMIT 14
        ''', (user_id, user_id, user_id, user_id, user_id, user_id))
        rows = c.fetchall()
        result = [dict(r) for r in rows]
        result.reverse()
        return result
    finally:
        conn.close()


def get_move_position_heatmap(user_id: int) -> list:
    """Get move frequency per board position for heatmap."""
    conn = get_db()
    c = conn.cursor()
    try:
        c.execute('''
            SELECT position, COUNT(*) as freq
            FROM moves
            WHERE player_id = ?
            GROUP BY position
            ORDER BY position
        ''', (user_id,))
        rows = c.fetchall()
        heatmap = [0] * 9
        for row in rows:
            heatmap[row['position']] = row['freq']
        return heatmap
    finally:
        conn.close()


def get_leaderboard(limit: int = 10) -> list:
    conn = get_db()
    c = conn.cursor()
    try:
        c.execute('''
            SELECT u.username, u.avatar_color,
                   ps.total_games, ps.wins, ps.losses, ps.draws,
                   ps.win_streak, ps.max_win_streak,
                   CASE WHEN ps.total_games > 0 
                        THEN ROUND(ps.wins * 100.0 / ps.total_games, 1)
                        ELSE 0 END as win_rate
            FROM player_stats ps
            JOIN users u ON ps.user_id = u.id
            WHERE ps.total_games > 0
            ORDER BY ps.wins DESC, win_rate DESC
            LIMIT ?
        ''', (limit,))
        return [dict(r) for r in c.fetchall()]
    finally:
        conn.close()


def get_global_stats() -> dict:
    conn = get_db()
    c = conn.cursor()
    try:
        c.execute('SELECT COUNT(*) as total FROM games WHERE ended_at IS NOT NULL')
        total_games = c.fetchone()['total']

        c.execute('SELECT COUNT(*) as total FROM users')
        total_users = c.fetchone()['total']

        c.execute('SELECT COUNT(*) as total FROM games WHERE is_draw = 1')
        total_draws = c.fetchone()['total']

        c.execute('SELECT AVG(moves_count) as avg FROM games WHERE ended_at IS NOT NULL')
        row = c.fetchone()
        avg_moves = round(row['avg'], 1) if row['avg'] else 0

        return {
            'total_games': total_games,
            'total_users': total_users,
            'total_draws': total_draws,
            'avg_moves': avg_moves,
        }
    finally:
        conn.close()
