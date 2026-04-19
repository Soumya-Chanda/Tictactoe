"""
Tic-Tac-Toe Web Application
Flask backend with all routes: auth, game, API, dashboard.
"""
from flask import (Flask, render_template, request, session,
                   redirect, url_for, jsonify)
from database.models import init_db
from auth import register_user, login_user, get_user_by_id
from game_logic import (new_board, apply_move, check_winner,
                        get_ai_move, board_to_string, string_to_board)
from game_service import (create_game, record_move, end_game,
                          update_player_stats, get_game,
                          get_player_stats, get_recent_games,
                          get_win_loss_over_time, get_move_position_heatmap,
                          get_leaderboard, get_global_stats)
import time
import os

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'ttt-super-secret-key-change-in-prod')


# ── Helpers ───────────────────────────────────────────────────────────────────

def login_required(f):
    from functools import wraps
    @wraps(f)
    def decorated(*args, **kwargs):
        if 'user_id' not in session:
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated


# ── Auth routes ───────────────────────────────────────────────────────────────

@app.route('/')
def index():
    if 'user_id' in session:
        return redirect(url_for('home'))
    return redirect(url_for('login'))


@app.route('/login', methods=['GET', 'POST'])
def login():
    if 'user_id' in session:
        return redirect(url_for('home'))
    error = None
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '')
        result = login_user(username, password)
        if result['success']:
            session['user_id'] = result['user']['id']
            session['username'] = result['user']['username']
            session['avatar_color'] = result['user']['avatar_color']
            return redirect(url_for('home'))
        error = result['message']
    return render_template('login.html', error=error)


@app.route('/register', methods=['GET', 'POST'])
def register():
    if 'user_id' in session:
        return redirect(url_for('home'))
    error = None
    success = None
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        email = request.form.get('email', '').strip()
        password = request.form.get('password', '')
        confirm = request.form.get('confirm_password', '')
        if password != confirm:
            error = 'Passwords do not match.'
        else:
            result = register_user(username, email, password)
            if result['success']:
                success = 'Account created! You can now log in.'
            else:
                error = result['message']
    return render_template('register.html', error=error, success=success)


@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))


# ── Main pages ────────────────────────────────────────────────────────────────

@app.route('/home')
@login_required
def home():
    stats = get_player_stats(session['user_id'])
    recent = get_recent_games(session['user_id'], limit=5)
    global_s = get_global_stats()
    return render_template('home.html',
                           stats=stats, recent=recent,
                           global_stats=global_s)


@app.route('/play')
@login_required
def play():
    return render_template('play.html')


@app.route('/profile', methods=['GET', 'POST'])
@login_required
def profile():
    from auth import verify_password, hash_password
    from database.models import get_db

    success = None
    error = None

    if request.method == 'POST':
        action = request.form.get('action')

        if action == 'change_color':
            color = request.form.get('color', '#6c63ff')
            allowed = ['#6c63ff','#f76a6a','#6af7c8','#fa8231','#00b8d9',
                       '#f7c86a','#ee0979','#43e97b','#f64f59','#12c2e9','#a18cd1','#ffecd2']
            if color in allowed:
                conn = get_db()
                conn.execute('UPDATE users SET avatar_color=? WHERE id=?',
                             (color, session['user_id']))
                conn.commit()
                conn.close()
                session['avatar_color'] = color
                success = 'Avatar color updated!'
            else:
                error = 'Invalid color.'

        elif action == 'change_password':
            current = request.form.get('current_password', '')
            new_pw = request.form.get('new_password', '')
            conn = get_db()
            row = conn.execute('SELECT password_hash FROM users WHERE id=?',
                               (session['user_id'],)).fetchone()
            conn.close()
            if not verify_password(current, row['password_hash']):
                error = 'Current password is incorrect.'
            elif len(new_pw) < 6:
                error = 'New password must be at least 6 characters.'
            else:
                conn = get_db()
                conn.execute('UPDATE users SET password_hash=? WHERE id=?',
                             (hash_password(new_pw), session['user_id']))
                conn.commit()
                conn.close()
                success = 'Password changed successfully!'

    user = get_user_by_id(session['user_id'])
    stats = get_player_stats(session['user_id'])
    return render_template('profile.html', user=user, stats=stats,
                           success=success, error=error)


@app.route('/dashboard')
@login_required
def dashboard():
    stats = get_player_stats(session['user_id'])
    recent = get_recent_games(session['user_id'], limit=15)
    timeline = get_win_loss_over_time(session['user_id'])
    heatmap = get_move_position_heatmap(session['user_id'])
    leaderboard = get_leaderboard(10)
    global_s = get_global_stats()
    return render_template('dashboard.html',
                           stats=stats, recent=recent,
                           timeline=timeline, heatmap=heatmap,
                           leaderboard=leaderboard,
                           global_stats=global_s)


@app.route('/game/<int:game_id>')
@login_required
def game(game_id):
    g = get_game(game_id)
    if not g:
        return redirect(url_for('home'))
    if g['player1_id'] != session['user_id'] and g['player2_id'] != session['user_id']:
        return redirect(url_for('home'))
    return render_template('game.html', game=g)


# ── Game API ──────────────────────────────────────────────────────────────────

@app.route('/api/game/start', methods=['POST'])
@login_required
def api_start_game():
    data = request.get_json()
    mode = data.get('mode', 'pvp')          # 'pvp' or 'pvc'
    difficulty = data.get('difficulty', 'medium')
    player2_id = data.get('player2_id', None)

    if mode == 'pvc':
        game_id = create_game(session['user_id'], 'pvc', None, difficulty)
    else:
        game_id = create_game(session['user_id'], 'pvp', player2_id, 'none')

    # Store game state in session
    session[f'game_{game_id}'] = {
        'board': new_board(),
        'current_turn': 'X',
        'mode': mode,
        'difficulty': difficulty,
        'move_number': 0,
        'start_time': time.time(),
        'status': 'active',
    }

    return jsonify({'success': True, 'game_id': game_id})


@app.route('/api/game/<int:game_id>/move', methods=['POST'])
@login_required
def api_make_move(game_id):
    data = request.get_json()
    position = data.get('position')
    player_symbol = data.get('symbol', 'X')

    key = f'game_{game_id}'
    state = session.get(key)
    if not state or state['status'] != 'active':
        return jsonify({'success': False, 'message': 'Game not active'})

    board = state['board']

    # Validate move
    if board[position] is not None:
        return jsonify({'success': False, 'message': 'Cell already taken'})

    # Apply human move
    board = apply_move(board, position, player_symbol)
    state['move_number'] += 1
    move_num = state['move_number']

    record_move(game_id, session['user_id'], position,
                player_symbol, move_num, board_to_string(board))

    result = check_winner(board)

    ai_move_pos = None

    # If PvC and game not over, AI moves
    if state['mode'] == 'pvc' and not result['winner'] and not result['is_draw']:
        ai_pos = get_ai_move(board, state['difficulty'])
        board = apply_move(board, ai_pos, 'O')
        state['move_number'] += 1
        record_move(game_id, None, ai_pos, 'O', state['move_number'],
                    board_to_string(board))
        ai_move_pos = ai_pos
        result = check_winner(board)

    state['board'] = board
    session[key] = state

    response = {
        'success': True,
        'board': board,
        'result': result,
        'ai_move': ai_move_pos,
        'move_number': state['move_number'],
    }

    # Game over?
    if result['winner'] or result['is_draw']:
        state['status'] = 'finished'
        session[key] = state
        duration = int(time.time() - state['start_time'])

        g = get_game(game_id)
        winner_id = None
        if result['winner']:
            winner_id = session['user_id'] if result['winner'] == 'X' else None

        end_game(game_id, winner_id, result['is_draw'], duration)

        # Update stats for human player
        if result['is_draw']:
            outcome = 'draw'
        elif winner_id == session['user_id']:
            outcome = 'win'
        else:
            outcome = 'loss'

        update_player_stats(session['user_id'], outcome,
                            state['mode'], state['move_number'],
                            outcome == 'win')

        response['game_over'] = True
        response['outcome'] = outcome
    else:
        response['game_over'] = False

    return jsonify(response)


@app.route('/api/game/<int:game_id>/pvp_move', methods=['POST'])
@login_required
def api_pvp_move(game_id):
    """Handle a move in a PvP (same device) game."""
    data = request.get_json()
    position = data.get('position')
    symbol = data.get('symbol')

    key = f'game_{game_id}'
    state = session.get(key)
    if not state or state['status'] != 'active':
        return jsonify({'success': False, 'message': 'Game not active'})

    board = state['board']
    if board[position] is not None:
        return jsonify({'success': False, 'message': 'Cell taken'})

    board = apply_move(board, position, symbol)
    state['move_number'] += 1
    state['current_turn'] = 'O' if symbol == 'X' else 'X'

    record_move(game_id, session['user_id'], position,
                symbol, state['move_number'], board_to_string(board))

    result = check_winner(board)
    state['board'] = board
    session[key] = state

    response = {
        'success': True,
        'board': board,
        'result': result,
        'current_turn': state['current_turn'],
        'move_number': state['move_number'],
    }

    if result['winner'] or result['is_draw']:
        state['status'] = 'finished'
        session[key] = state
        duration = int(time.time() - state['start_time'])

        winner_id = session['user_id'] if result['winner'] else None
        end_game(game_id, winner_id, result['is_draw'], duration)
        update_player_stats(session['user_id'],
                            'draw' if result['is_draw'] else ('win' if result['winner'] else 'loss'),
                            'pvp', state['move_number'], bool(result['winner']))
        response['game_over'] = True
    else:
        response['game_over'] = False

    return jsonify(response)


@app.route('/api/game/<int:game_id>/resign', methods=['POST'])
@login_required
def api_resign(game_id):
    key = f'game_{game_id}'
    state = session.get(key)
    if state:
        state['status'] = 'finished'
        session[key] = state
        duration = int(time.time() - state.get('start_time', time.time()))
        end_game(game_id, None, False, duration)
        update_player_stats(session['user_id'], 'loss',
                            state.get('mode', 'pvp'),
                            state.get('move_number', 0), False)
    return jsonify({'success': True})


# ── Dashboard API ─────────────────────────────────────────────────────────────

@app.route('/api/dashboard/stats')
@login_required
def api_dashboard_stats():
    stats = get_player_stats(session['user_id'])
    timeline = get_win_loss_over_time(session['user_id'])
    heatmap = get_move_position_heatmap(session['user_id'])
    leaderboard = get_leaderboard(10)
    return jsonify({
        'stats': stats,
        'timeline': timeline,
        'heatmap': heatmap,
        'leaderboard': leaderboard,
    })


# ── Error handlers ────────────────────────────────────────────────────────────

@app.errorhandler(404)
def not_found(e):
    return render_template('error.html', code=404,
                           msg='Page not found.'), 404

@app.errorhandler(500)
def server_error(e):
    return render_template('error.html', code=500,
                           msg='Internal server error.'), 500

@app.route('/health')
def health():
    return jsonify({'status': 'ok', 'app': 'TicTacMaster'})


# ── Run ───────────────────────────────────────────────────────────────────────

if __name__ == '__main__':
    init_db()
    app.run(debug=True, host='0.0.0.0', port=5000)
