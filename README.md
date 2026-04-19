# ✕○ TicTacMaster — Full-Stack Tic-Tac-Toe Web Application

A complete, production-quality Tic-Tac-Toe web application built entirely in Python (Flask) with a beautiful dark UI, player authentication, AI opponent, analytics dashboard, and SQLite database.

---

## 📁 Project Structure

```
tictactoe/
│
├── app.py                  ← Main Flask application (all routes)
├── game_logic.py           ← Game engine: rules, win detection, AI (Minimax)
├── game_service.py         ← Database operations: games, moves, stats
├── auth.py                 ← Auth: register, login, password hashing (SHA-256 + salt)
├── requirements.txt        ← Python dependencies
│
├── database/
│   ├── __init__.py
│   ├── models.py           ← SQLite schema + init_db()
│   └── tictactoe.db        ← Auto-created on first run
│
└── templates/
    ├── base.html           ← Shared layout, nav, global CSS
    ├── login.html          ← Login page
    ├── register.html       ← Registration page
    ├── home.html           ← Home dashboard (stats + recent games)
    ├── play.html           ← Game board (PvP + PvC)
    └── dashboard.html      ← Analytics dashboard with charts
```

---

## 🚀 Setup & Run

### 1. Install dependencies

```bash
cd tictactoe
pip install -r requirements.txt
```

### 2. Run the application

```bash
python app.py
```

The app will start at **http://localhost:5000**

> The SQLite database (`tictactoe.db`) is automatically created on first run inside the `database/` folder.

---

## 🎮 Features

### Authentication
- User registration with username, email, and password
- Passwords hashed with SHA-256 + random salt (no plaintext storage)
- Persistent sessions via Flask session cookies
- Unique avatar color assigned per user

### Game Modes
| Mode | Description |
|------|-------------|
| **Player vs Computer** | Play against AI with Easy / Medium / Hard difficulty |
| **Player vs Player** | Two players take turns on the same device |

### AI Engine (Minimax)
- **Easy**: 70% random moves
- **Medium**: Blocks/wins when possible, otherwise 40% random
- **Hard**: Full Minimax with alpha-beta pruning (unbeatable)

### Win Detection
- All 8 winning combinations checked after every move
- Winning cells are highlighted with a gold pulse animation
- Draw detection when board is full

### Dashboard Analytics
All charts powered by Chart.js, data computed in Python:

| Chart | Description |
|-------|-------------|
| **Win/Loss Timeline** | Line chart — last 14 days of results |
| **Results Donut** | Wins / Losses / Draws breakdown |
| **PvP vs PvC Bar** | Mode-specific win/loss/draw comparison |
| **Move Heatmap** | 3×3 grid showing which cells you play most |
| **Leaderboard** | Top players ranked by wins + win rate |
| **Recent Games** | Last 15 game results with opponent and outcome |

---

## 🗄️ Database Schema

### `users`
| Column | Type | Description |
|--------|------|-------------|
| id | INTEGER | Primary key |
| username | TEXT | Unique username |
| email | TEXT | Unique email |
| password_hash | TEXT | salt:sha256hash |
| avatar_color | TEXT | Hex color for avatar |
| created_at | TIMESTAMP | Registration time |

### `games`
| Column | Type | Description |
|--------|------|-------------|
| id | INTEGER | Primary key |
| player1_id | INTEGER | FK → users |
| player2_id | INTEGER | FK → users (NULL for PvC) |
| game_mode | TEXT | 'pvp' or 'pvc' |
| winner_id | INTEGER | FK → users (NULL = draw/unfinished) |
| is_draw | INTEGER | 1 if draw |
| board_state | TEXT | Comma-separated 9-cell state |
| moves_count | INTEGER | Total moves made |
| duration_seconds | INTEGER | Game duration |
| ai_difficulty | TEXT | 'easy'/'medium'/'hard' |
| created_at | TIMESTAMP | Game start time |
| ended_at | TIMESTAMP | Game end time |

### `moves`
| Column | Type | Description |
|--------|------|-------------|
| id | INTEGER | Primary key |
| game_id | INTEGER | FK → games |
| player_id | INTEGER | FK → users (NULL for AI) |
| position | INTEGER | 0–8 board cell index |
| symbol | TEXT | 'X' or 'O' |
| move_number | INTEGER | Sequential move number |

### `player_stats`
| Column | Type | Description |
|--------|------|-------------|
| user_id | INTEGER | FK → users (unique) |
| total_games | INTEGER | All games played |
| wins / losses / draws | INTEGER | Overall results |
| pvp_wins / pvp_losses / pvp_draws | INTEGER | PvP breakdown |
| pvc_wins / pvc_losses / pvc_draws | INTEGER | PvC breakdown |
| win_streak | INTEGER | Current streak |
| max_win_streak | INTEGER | Best streak ever |
| total_moves | INTEGER | Lifetime moves made |
| fastest_win_moves | INTEGER | Fewest moves to win |

---

## 🔌 API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/` | Redirect to home or login |
| GET/POST | `/login` | Login page |
| GET/POST | `/register` | Registration page |
| GET | `/logout` | Clear session |
| GET | `/home` | Home page with stats |
| GET | `/play` | Game selection + board |
| GET | `/dashboard` | Analytics dashboard |
| POST | `/api/game/start` | Start a new game |
| POST | `/api/game/<id>/move` | Make a move (PvC) |
| POST | `/api/game/<id>/pvp_move` | Make a move (PvP) |
| POST | `/api/game/<id>/resign` | Resign current game |
| GET | `/api/dashboard/stats` | JSON stats for user |

---

## 🛠️ Configuration

Set these environment variables before running in production:

```bash
export SECRET_KEY="your-strong-secret-key-here"
```

For production deployment, use Gunicorn:

```bash
pip install gunicorn
gunicorn -w 4 -b 0.0.0.0:5000 app:app
```

---

## 🎨 Tech Stack

| Layer | Tech |
|-------|------|
| Backend | Python 3.10+, Flask 3.x |
| Database | SQLite (via stdlib `sqlite3`) |
| Frontend | Vanilla HTML/CSS/JS (no framework) |
| Charts | Chart.js 4.4 (CDN) |
| Fonts | Google Fonts (Syne + DM Sans) |
| AI | Minimax + Alpha-Beta Pruning |
| Auth | SHA-256 + random salt |
