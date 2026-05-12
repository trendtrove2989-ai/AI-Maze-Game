import random
import heapq
from collections import deque
import tkinter as tk
from tkinter import Canvas
from flask import Flask, jsonify, request
from flask_cors import CORS
import cv2
import numpy as np
# ==========================================
# 1. MAZE GENERATOR (DFS with Loops)
# ==========================================
class MazeGenerator:
    def __init__(self, w, h):
        self.w = w if w % 2 != 0 else w + 1
        self.h = h if h % 2 != 0 else h + 1
        self.grid = [[1 for _ in range(self.w)] for _ in range(self.h)]

    def generate_dfs(self):
        self.grid = [[1 for _ in range(self.w)] for _ in range(self.h)]
        stack = [(1, 1)]
        self.grid[1][1] = 0

        while stack:
            cx, cy = stack[-1]
            neighbors = []
            for dx, dy in [(0, 2), (2, 0), (0, -2), (-2, 0)]:
                nx, ny = cx + dx, cy + dy
                if 0 < nx < self.w - 1 and 0 < ny < self.h - 1 and self.grid[ny][nx] == 1:
                    neighbors.append((nx, ny, dx // 2, dy // 2))

            if neighbors:
                nx, ny, mx, my = random.choice(neighbors)
                self.grid[cy + my][cx + mx] = 0
                self.grid[ny][nx] = 0
                stack.append((nx, ny))
            else:
                stack.pop()

        # LOOP CREATOR: Knock down random walls to create multiple routes
        for _ in range((self.w * self.h) // 15):
            rx = random.randint(1, self.w - 2)
            ry = random.randint(1, self.h - 2)
            if self.grid[ry][rx] == 1:
                if self.grid[ry][rx - 1] == 0 and self.grid[ry][rx + 1] == 0:
                    self.grid[ry][rx] = 0
                elif self.grid[ry - 1][rx] == 0 and self.grid[ry + 1][rx] == 0:
                    self.grid[ry][rx] = 0

        return self.grid


# ==========================================
# 2. CSP COIN PLACEMENT
# ==========================================
class CSPModule:
    @staticmethod
    def place_coins(grid, num_coins, min_dist, avoid_positions):
        empty_cells = [(x, y) for y in range(len(grid)) for x in range(len(grid[0])) if grid[y][x] == 0]
        coins = []
        for _ in range(300):
            if len(coins) == num_coins:
                break
            cand = random.choice(empty_cells)
            if cand in avoid_positions:
                continue
            valid = True
            for cx, cy in coins:
                if abs(cx - cand[0]) + abs(cy - cand[1]) < min_dist:
                    valid = False
                    break
            if valid:
                coins.append(cand)
        return coins


# ==========================================
# 3. AI PLAYER — INTELLIGENT BFS PLANNER
# ==========================================
class AIPlayer:
    """
    Strategy engine with three phases:
      DANGER  — Monster within 5 steps: flee to maximise distance using full BFS map.
      PLAN    — Pick the highest-value safe target (coin or exit) and follow a
                time-safe path where we always arrive BEFORE the monster.
      FALLBACK— No safe target reachable: drift toward best coin ignoring monster,
                still preferring cells farther from monster.
    """

    # ---- Low-level BFS helpers -----------------------------------------

    @staticmethod
    def bfs_distances(grid, start):
        """Return {cell: steps} for every cell reachable from start."""
        dist = {start: 0}
        q = deque([start])
        while q:
            pos = q.popleft()
            for dx, dy in [(0, 1), (1, 0), (0, -1), (-1, 0)]:
                nb = (pos[0] + dx, pos[1] + dy)
                x, y = nb
                if (
                    0 <= x < len(grid[0])
                    and 0 <= y < len(grid)
                    and grid[y][x] in [0, 2]
                    and nb not in dist
                ):
                    dist[nb] = dist[pos] + 1
                    q.append(nb)
        return dist

    @staticmethod
    def bfs_path(grid, start, goal):
        """Shortest path from start to goal (unrestricted). Returns [] if none."""
        if start == goal:
            return [start]
        prev = {start: None}
        q = deque([start])
        while q:
            pos = q.popleft()
            if pos == goal:
                break
            for dx, dy in [(0, 1), (1, 0), (0, -1), (-1, 0)]:
                nb = (pos[0] + dx, pos[1] + dy)
                x, y = nb
                if (
                    0 <= x < len(grid[0])
                    and 0 <= y < len(grid)
                    and grid[y][x] in [0, 2]
                    and nb not in prev
                ):
                    prev[nb] = pos
                    q.append(nb)
        if goal not in prev:
            return []
        path, cur = [], goal
        while cur is not None:
            path.append(cur)
            cur = prev[cur]
        path.reverse()
        return path

    @staticmethod
    def time_safe_bfs(grid, start, goal, monster_dist_map, safety_margin=1):
        """
        BFS that only steps onto a cell (x, y) if the monster needs MORE steps to
        reach it than we do (our_time + safety_margin < monster_time).
        This guarantees we never walk somewhere the monster can intercept us.
        """
        # State: (position, time_elapsed)
        prev = {start: None}
        q = deque([(start, 0)])
        while q:
            pos, t = q.popleft()
            if pos == goal:
                break
            for dx, dy in [(0, 1), (1, 0), (0, -1), (-1, 0)]:
                nb = (pos[0] + dx, pos[1] + dy)
                x, y = nb
                nt = t + 1
                if (
                    0 <= x < len(grid[0])
                    and 0 <= y < len(grid)
                    and grid[y][x] in [0, 2]
                    and nb not in prev
                    and monster_dist_map.get(nb, 9999) > nt + safety_margin
                ):
                    prev[nb] = pos
                    q.append((nb, nt))
        if goal not in prev:
            return []
        path, cur = [], goal
        while cur is not None:
            path.append(cur)
            cur = prev[cur]
        path.reverse()
        return path

    # ---- High-level strategy -------------------------------------------

    @staticmethod
    def score_target(target, ai_dist_map, monster_dist_map, bonus=0):
        """
        Returns a float score for visiting 'target'.
        Higher = better. Returns -inf if unreachable or unsafe.
        """
        d_ai  = ai_dist_map.get(target, 9999)
        d_mon = monster_dist_map.get(target, 9999)
        if d_ai == 9999:
            return float('-inf')
        lead = d_mon - d_ai          # positive = we arrive first
        if lead <= 0:
            return float('-inf')     # monster wins the race — skip
        # Reward big leads and short distances
        return lead * 25 - d_ai * 8 + bonus

    @staticmethod
    def get_best_move(state):
        grid       = state.grid
        ai_pos     = state.ai_pos
        m_pos      = state.m_pos

        # ── Pre-compute full BFS distance maps ──────────────────────────
        ai_dists      = AIPlayer.bfs_distances(grid, ai_pos)
        monster_dists = AIPlayer.bfs_distances(grid, m_pos)
        monster_to_ai = monster_dists.get(ai_pos, 9999)

        # ── PHASE 1: DANGER — Monster is very close, run! ───────────────
        if monster_to_ai <= 5:
            state.ai_planned_path = []          # Cancel any existing plan
            state.ai_plan_target  = None

            moves = []
            for dx, dy in [(0, 1), (1, 0), (0, -1), (-1, 0)]:
                nb = (ai_pos[0] + dx, ai_pos[1] + dy)
                x, y = nb
                if (
                    0 <= x < len(grid[0])
                    and 0 <= y < len(grid)
                    and grid[y][x] in [0, 2]
                ):
                    moves.append(nb)

            if not moves:
                return ai_pos

            # Among legal moves pick the one farthest from monster.
            # Break ties by preferring moves that also lead toward a coin.
            def flee_score(p):
                dist_from_monster = monster_dists.get(p, 0)
                # secondary: closeness to nearest coin (so we don't run into dead ends)
                coin_bonus = 0
                if state.coins:
                    coin_bonus = -min(abs(p[0]-c[0]) + abs(p[1]-c[1]) for c in state.coins) * 0.5
                return dist_from_monster + coin_bonus

            return max(moves, key=flee_score)

        # ── PHASE 2: CHECK existing planned path is still valid ─────────
        if (
            state.ai_planned_path
            and len(state.ai_planned_path) > 1
            and state.ai_planned_path[0] == ai_pos        # plan still current
        ):
            next_step = state.ai_planned_path[1]
            x, y = next_step
            if (
                0 <= x < len(grid[0])
                and 0 <= y < len(grid)
                and grid[y][x] in [0, 2]
                and monster_dists.get(next_step, 9999) > 2  # still safe
            ):
                state.ai_planned_path = state.ai_planned_path[1:]
                return next_step
            else:
                # Path invalidated — force full re-plan
                state.ai_planned_path = []
                state.ai_plan_target  = None

        # ── PHASE 3: PLAN — Score all targets and pick the best ─────────
        candidates = []

        # Coins
        for coin in state.coins:
            s = AIPlayer.score_target(coin, ai_dists, monster_dists, bonus=0)
            if s > float('-inf'):
                candidates.append((s, coin))

        # AI's assigned exit only (top-left) — massive bonus so it rushes there
        if state.exits_unlocked:
            s = AIPlayer.score_target(state.ai_exit, ai_dists, monster_dists, bonus=600)
            if s > float('-inf'):
                candidates.append((s, state.ai_exit))

        # Sort best-first
        candidates.sort(key=lambda x: -x[0])

        # Try to build a time-safe path to each candidate in order
        for score, target in candidates:
            path = AIPlayer.time_safe_bfs(grid, ai_pos, target, monster_dists, safety_margin=1)
            if len(path) >= 2:
                state.ai_planned_path = path
                state.ai_plan_target  = target
                return path[1]

        # ── PHASE 4: FALLBACK — No safe route exists ────────────────────
        # Navigate toward the closest reachable coin (ignoring safety constraint)
        # but still prefer moves that are farther from the monster.
        state.ai_planned_path = []
        state.ai_plan_target  = None

        best_fallback = None
        if state.coins:
            reachable_coins = [(ai_dists.get(c, 9999), c) for c in state.coins if c in ai_dists]
            if reachable_coins:
                _, closest_coin = min(reachable_coins)
                fallback_path = AIPlayer.bfs_path(grid, ai_pos, closest_coin)
                if len(fallback_path) >= 2:
                    best_fallback = fallback_path[1]

        # Also consider legal moves ranked by monster distance
        moves = []
        for dx, dy in [(0, 1), (1, 0), (0, -1), (-1, 0)]:
            nb = (ai_pos[0] + dx, ai_pos[1] + dy)
            x, y = nb
            if (
                0 <= x < len(grid[0])
                and 0 <= y < len(grid)
                and grid[y][x] in [0, 2]
            ):
                moves.append(nb)

        if best_fallback and best_fallback in moves:
            # Prefer it only if it's not directly into danger
            if monster_dists.get(best_fallback, 9999) > 3:
                return best_fallback

        if moves:
            return max(moves, key=lambda p: monster_dists.get(p, 0))

        return ai_pos   # completely trapped — stay put


# ==========================================
# 4. MONSTER AGENT (A* SEARCH)
# ==========================================
class MonsterAgent:
    @staticmethod
    def a_star(grid, start, goal):
        q = []
        heapq.heappush(q, (0, start))
        came_from = {}
        cost = {start: 0}

        while q:
            _, curr = heapq.heappop(q)
            if curr == goal:
                break
            for dx, dy in [(0, 1), (1, 0), (0, -1), (-1, 0)]:
                nx, ny = curr[0] + dx, curr[1] + dy
                if (
                    0 <= nx < len(grid[0])
                    and 0 <= ny < len(grid)
                    and grid[ny][nx] in [0, 2]
                ):
                    nc = cost[curr] + 1
                    if (nx, ny) not in cost or nc < cost[(nx, ny)]:
                        cost[(nx, ny)] = nc
                        priority = nc + abs(goal[0] - nx) + abs(goal[1] - ny)
                        heapq.heappush(q, (priority, (nx, ny)))
                        came_from[(nx, ny)] = curr

        if goal not in came_from:
            return []
        curr = goal
        path = []
        while curr != start:
            path.append(curr)
            curr = came_from[curr]
        path.reverse()
        return path


# ==========================================
# 5. GAME STATE & MAIN LOGIC
# ==========================================
class GameState:
    def __init__(self, w=21, h=21, custom_grid=None):
        self.mg = MazeGenerator(w, h)
        if custom_grid:
            self.grid = custom_grid
            self.mg.w = len(custom_grid[0])
            self.mg.h = len(custom_grid)
        else:
            self.grid = self.mg.generate_dfs()

        self.h_pos = (1, 1)
        self.ai_pos = (self.mg.w - 2, self.mg.h - 2)
        self.ai_last_pos = self.ai_pos
        self.ai_planned_path = []
        self.ai_plan_target = None
        self.status = "playing"

        self.grid[1][1] = 0
        self.grid[self.mg.h - 2][self.mg.w - 2] = 0

        while True:
            mx = random.randrange(1, self.mg.w, 2)
            my = random.randrange(1, self.mg.h, 2)
            if (
                self.grid[my][mx] == 0
                and abs(mx - self.h_pos[0]) + abs(my - self.h_pos[1]) >= 12
            ):
                self.m_pos = (mx, my)
                break

        self.h_exit = (self.mg.w - 2, self.mg.h - 1)
        self.ai_exit = (1, 0)
        self.exits = [self.h_exit, self.ai_exit]
        self.exits_unlocked = False

        self.coins = CSPModule.place_coins(
            self.grid, 8, 4, [self.h_pos, self.ai_pos, self.m_pos]
        )
        self.h_score = 0
        self.ai_score = 0
        self.turns = 0

    def step_game(self):
        if self.status != "playing":
            return

        if self.ai_pos != (-1, -1):
            prev_ai = self.ai_pos
            self.ai_pos = AIPlayer.get_best_move(self)
            self.ai_last_pos = prev_ai

            if self.ai_pos in self.coins:
                self.coins.remove(self.ai_pos)
                self.ai_score += 1

            if self.exits_unlocked and self.ai_pos == self.ai_exit:
                self.status = "ai_win"
                return

        if self.h_pos != (-1, -1) and self.ai_pos != (-1, -1):
            target = self.h_pos if self.h_score >= self.ai_score else self.ai_pos
        elif self.h_pos != (-1, -1):
            target = self.h_pos
        elif self.ai_pos != (-1, -1):
            target = self.ai_pos
        else:
            target = self.m_pos

        m_path = MonsterAgent.a_star(self.grid, self.m_pos, target)
        if m_path:
            self.m_pos = m_path[0]

        if self.h_pos == self.m_pos:
            self.status = "lose"
            self.h_pos = (-1, -1)
            
        if self.ai_pos == self.m_pos:
            self.ai_pos = (-1, -1)

        self.turns += 1
        if self.turns >= 15 and not self.exits_unlocked:
            self.exits_unlocked = True
            for ex, ey in self.exits:
                self.grid[ey][ex] = 2

    def move_human(self, dx, dy):
        if self.status != "playing":
            return False

        nx, ny = self.h_pos[0] + dx, self.h_pos[1] + dy
        if (
            0 <= nx < len(self.grid[0])
            and 0 <= ny < len(self.grid)
            and self.grid[ny][nx] in [0, 2]
        ):
            self.h_pos = (nx, ny)

            # Human wins only by reaching THEIR exit (bottom-right)
            if self.h_pos == self.h_exit and self.exits_unlocked:
                self.status = "win"
                return True

            if self.h_pos in self.coins:
                self.coins.remove(self.h_pos)
                self.h_score += 1

            # Death check: human walks into monster
            if self.h_pos == self.m_pos:
                self.status = "lose"
                self.h_pos  = (-1, -1)
                return True

            self.step_game()
            return True
        return False


# ==========================================
# WEB API & FALLBACK TKINTER
# ==========================================
app        = Flask(__name__)
CORS(app)
game_state = GameState(25, 25)


def _state_dict():
    return {
        "grid":           game_state.grid,
        "h_pos":          game_state.h_pos,
        "ai_pos":         game_state.ai_pos,
        "ai_plan_target": game_state.ai_plan_target,
        "m_pos":          game_state.m_pos,
        "coins":          game_state.coins,
        "scores":         {"h": game_state.h_score, "ai": game_state.ai_score},
        "turns":          game_state.turns,
        "status":         game_state.status,
        "exits_unlocked": game_state.exits_unlocked,
        "h_exit":         game_state.h_exit,
        "ai_exit":        game_state.ai_exit,
    }


@app.route('/api/state', methods=['GET'])
def get_state():
    return jsonify(_state_dict())


@app.route('/api/move', methods=['POST'])
def make_move():
    if game_state.status == "playing":
        data      = request.json
        direction = data.get('direction')
        dx, dy    = 0, 0
        if   direction == 'up':    dy = -1
        elif direction == 'down':  dy =  1
        elif direction == 'left':  dx = -1
        elif direction == 'right': dx =  1
        game_state.move_human(dx, dy)
    return jsonify(_state_dict())


# Add methods=['POST', 'GET'] to fix the error!
@app.route('/api/reset', methods=['POST', 'GET'])
def reset_game():
    global game_state # or whatever your global state variable is called
    
    # 1. Reset your AI and Human positions here
    # 2. Reset the score and turns here
    # 3. Set status back to 'playing'
    
    return jsonify(game_state)
@app.route('/api/upload', methods=['POST'])
def upload_maze():
    global game_state
    if 'file' in request.files:
        file = request.files['file']
        npimg = np.frombuffer(file.read(), np.uint8)
        img = cv2.imdecode(npimg, cv2.IMREAD_GRAYSCALE)
        img = cv2.resize(img, (25, 25), interpolation=cv2.INTER_NEAREST)
        _, thresh = cv2.threshold(img, 127, 1, cv2.THRESH_BINARY_INV)
        custom_grid = thresh.tolist()
        
        for r in range(25):
            custom_grid[r][0] = 1
            custom_grid[r][24] = 1
            custom_grid[0][r] = 1
            custom_grid[24][r] = 1
            
        custom_grid[1][1] = 0
        custom_grid[23][23] = 0
        
        game_state = GameState(25, 25, custom_grid)
        
    return jsonify(_state_dict())
def reset_game():
    global game_state
    game_state = GameState(25, 25)
    return get_state()


# ==========================================
# FALLBACK: TKINTER VISUALISER
# ==========================================
if __name__ == "__main__":
    import sys

    if len(sys.argv) == 1 or (len(sys.argv) > 1 and sys.argv[1] == "web"):
        print("Starting Game Server on port 5000 …")
        app.run(port=5000, debug=True)
    else:
        print("Running fallback Tkinter board.")

        class GameApp:
            def __init__(self, root):
                self.root = root
                self.cs   = 25
                self.c    = Canvas(
                    root,
                    width  = game_state.mg.w * self.cs,
                    height = game_state.mg.h * self.cs,
                    bg     = "#1e293b",
                )
                self.c.pack()
                self.root.bind("<Key>", self.human_move)
                self.draw()

            def draw(self):
                self.c.delete("all")
                for y in range(game_state.mg.h):
                    for x in range(game_state.mg.w):
                        cell = game_state.grid[y][x]
                        color = (
                            "#0f172a" if cell == 1
                            else "#a855f7" if cell == 2
                            else "#e2e8f0"
                        )
                        self.c.create_rectangle(
                            x * self.cs, y * self.cs,
                            (x + 1) * self.cs, (y + 1) * self.cs,
                            fill=color, outline="",
                        )

                # Draw AI planned path (faint green tint)
                for px, py in game_state.ai_planned_path[1:]:
                    self.c.create_rectangle(
                        px * self.cs + 6, py * self.cs + 6,
                        (px + 1) * self.cs - 6, (py + 1) * self.cs - 6,
                        fill="#166534", outline="",
                    )

                for cx, cy in game_state.coins:
                    self.c.create_oval(
                        cx * self.cs + 4, cy * self.cs + 4,
                        (cx + 1) * self.cs - 4, (cy + 1) * self.cs - 4,
                        fill="#eab308",
                    )

                if game_state.h_pos != (-1, -1):
                    hx, hy = game_state.h_pos
                    self.c.create_rectangle(
                        hx * self.cs + 2, hy * self.cs + 2,
                        (hx + 1) * self.cs - 2, (hy + 1) * self.cs - 2,
                        fill="#3b82f6",
                    )

                ax, ay = game_state.ai_pos
                self.c.create_rectangle(
                    ax * self.cs + 2, ay * self.cs + 2,
                    (ax + 1) * self.cs - 2, (ay + 1) * self.cs - 2,
                    fill="#22c55e",
                )

                mx, my = game_state.m_pos
                self.c.create_rectangle(
                    mx * self.cs + 2, my * self.cs + 2,
                    (mx + 1) * self.cs - 2, (my + 1) * self.cs - 2,
                    fill="#ef4444",
                )

                # Status overlay
                if game_state.status != "playing":
                    msg = {
                        "win":    "YOU WIN!",
                        "lose":   "YOU LOSE!",
                        "ai_win": "AI WINS!",
                    }.get(game_state.status, game_state.status.upper())
                    self.c.create_text(
                        (game_state.mg.w * self.cs) // 2,
                        (game_state.mg.h * self.cs) // 2,
                        text=msg, fill="white", font=("Arial", 30, "bold"),
                    )

                # HUD
                self.c.create_text(
                    10, 10,
                    text=(
                        f"You: {game_state.h_score}  AI: {game_state.ai_score}  "
                        f"Turn: {game_state.turns}  "
                        f"Exit: {'OPEN' if game_state.exits_unlocked else f'in {15 - game_state.turns}t'}"
                    ),
                    fill="white", font=("Arial", 11), anchor="nw",
                )

            def human_move(self, event):
                dx, dy = 0, 0
                if   event.keysym == "Up":    dy = -1
                elif event.keysym == "Down":  dy =  1
                elif event.keysym == "Left":  dx = -1
                elif event.keysym == "Right": dx =  1
                if dx != 0 or dy != 0:
                    game_state.move_human(dx, dy)
                    self.draw()

        root = tk.Tk()
        root.title("Maze AI — Intelligent BFS Agent")
        gui = GameApp(root)
        root.mainloop()