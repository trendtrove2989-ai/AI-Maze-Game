<!-- HERO BANNER -->
<div align="center">
  <img src="https://capsule-render.vercel.app/api?type=waving&color=gradient&height=250&section=header&text=Intelligent%20Multi-Agent%20Maze&fontSize=50&animation=fadeIn&fontAlignY=38&desc=A%20Next-Gen%20AI%20Survival%20Game&descAlignY=55&descAlign=50" alt="Header Banner" />
</div>

<!-- BADGES -->
<div align="center">
  <a href="https://python.org"><img src="https://img.shields.io/badge/Python-3776AB?style=for-the-badge&logo=python&logoColor=white" alt="Python"/></a>
  <a href="https://flask.palletsprojects.com/"><img src="https://img.shields.io/badge/Flask-000000?style=for-the-badge&logo=flask&logoColor=white" alt="Flask"/></a>
  <a href="https://opencv.org/"><img src="https://img.shields.io/badge/OpenCV-5C3EE8?style=for-the-badge&logo=opencv&logoColor=white" alt="OpenCV"/></a>
  <a href="https://threejs.org/"><img src="https://img.shields.io/badge/Three.js-000000?style=for-the-badge&logo=threedotjs&logoColor=white" alt="Three.js"/></a>
  <a href="https://greensock.com/gsap/"><img src="https://img.shields.io/badge/GSAP-88CE02?style=for-the-badge&logo=greensock&logoColor=white" alt="GSAP"/></a>
</div>

<br />

<div align="center">
  <h3>
    <a href="#-about-the-project">About</a>
    <span> | </span>
    <a href="#-key-features">Features</a>
    <span> | </span>
    <a href="#-tech-stack">Tech Stack</a>
    <span> | </span>
    <a href="#-gameplay--controls">Gameplay</a>
    <span> | </span>
    <a href="#-api-architecture">API</a>
  </h3>
</div>

<br />

## 🌌 About The Project

Welcome to the **Intelligent Multi-Agent Maze Game**! This full-stack web application pits you against highly intelligent, autonomous agents inside a dynamically generated environment. Wrapping complex mathematical pathfinding algorithms in a premium, glassmorphic user interface, it delivers a visually stunning and deeply competitive experience.

> **"Navigate the maze. Outsmart the AI. Escape the Monster."**

<div align="center">
  <!-- REPLACE THIS IMAGE SRC WITH YOUR ACTUAL GAMEPLAY GIF -->
  <img src="https://via.placeholder.com/800x450/0f172a/38bdf8?text=Drop+Your+Gameplay+GIF+Here!" alt="Gameplay Demo" width="100%" style="border-radius: 15px; box-shadow: 0 8px 32px rgba(0,0,0,0.5);"/>
</div>

---

## ✨ Key Features

<table>
  <tr>
    <td width="50%">
      <h3>🎲 Dynamic Procedural Generation</h3>
      <p>Every match features a brand-new, randomized maze generated using <b>Depth-First Search (DFS)</b> with an intelligent loop-creator to ensure multiple routing paths.</p>
    </td>
    <td width="50%">
      <h3>🤖 Multi-Agent AI System</h3>
      <p><b>The Monster:</b> Relentlessly tracks you using <b>A* Search</b> heuristic pathfinding.<br><b>The AI Competitor:</b> Uses a <b>Time-Safe BFS</b> engine to safely navigate, collect coins, and evade threats.</p>
    </td>
  </tr>
  <tr>
    <td width="50%">
      <h3>📸 Computer Vision Integration</h3>
      <p>Upload a physical drawing of a maze! The backend utilizes <b>OpenCV</b> binary thresholding to dynamically convert user-uploaded images into playable digital grids.</p>
    </td>
    <td width="50%">
      <h3>🎨 Premium Glassmorphic UI</h3>
      <p>Experience smooth, hardware-accelerated rendering with a <b>Three.js</b> 3D ambient background, fluid <b>GSAP</b> transitions, and custom spatial audio.</p>
    </td>
  </tr>
</table>

---

## 💻 Tech Stack

<div align="center">
  <p><b>Built with industry-standard frameworks and libraries:</b></p>
  <img src="https://skillicons.dev/icons?i=python,flask,js,html,css,threejs,github&perline=7" alt="Tech Stack Icons" />
</div>

<br>

*   **Backend Engineering:** Python 3, Flask, Flask-CORS, NumPy
*   **Computer Vision:** OpenCV (`cv2`)
*   **Frontend UI:** HTML5 Canvas, CSS3, Vanilla JS
*   **Visual Engine:** Three.js (3D Environment), GSAP (Animations)
*   **Core AI Algorithms:** DFS, BFS, A* Search, Constraint Satisfaction Problem (CSP)

---

## 🚀 Getting Started

To get a local copy up and running, follow these simple steps.

### Prerequisites
Ensure you have Python 3.x installed on your machine.

### Installation

**1. Clone the repository & install backend dependencies**
```bash
pip install Flask Flask-CORS opencv-python numpy
2. Start the Flask AI EngineBashpython game.py web
(Note: The web argument ensures the server opens its REST API on port 5000. Running without it launches a lightweight offline Tkinter GUI.)3. Launch the FrontendOpen index.html in any modern web browser. For optimal performance, use a local server extension (e.g., VS Code Live Server).🎮 Gameplay & Controls🟦 You (Blue): Navigate safely and collect coins.🟨 Coins (Yellow): Boost your score.🟩 AI Competitor (Green): Will try to steal your coins and escape first.🟥 Monster (Red): Will hunt whoever is closest or has the highest score.🟪 Exits (Purple): Unlock after 15 turns. Reach them to win!🔌 API ArchitectureThe backend operates as a headless game engine, responding to the frontend via the following REST endpoints:EndpointMethodDescription/api/stateRetrieves the current game matrix, entity coordinates, and score metrics./api/moveSubmits human movement vectors and calculates the subsequent game tick for all agents./api/resetRe-initializes the game state and generates a fresh procedural maze./api/uploadAccepts a multipart image file, processing it via OpenCV to output a custom binary maze grid.
