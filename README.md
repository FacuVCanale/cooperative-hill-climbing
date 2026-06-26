# cooperative-hill-climbing

Four autonomous agents explore a 2D mathematical landscape over TCP, competing to find the global maximum using gradient-based search, momentum, and inter-agent coordination to avoid redundant convergence.

---

## Overview

This project implements a **multi-agent cooperative hill-climbing** system in which four independent agents (hikers) navigate a continuous 2D search space returned by a remote server. Each agent maintains its own position, gradient estimates, and strategy state; a shared coordination layer prevents agents from converging to the same local optimum.

The server—provided by the course—exposes a TCP API: at each timestep the client sends a *direction + speed* directive for each agent, and the server replies with positional data `(x, y, z, ∂z/∂x, ∂z/∂y)`. The student-written client implements all search logic on top of that contract.

---

## Problem

Standard hill-climbing on multimodal functions gets stuck in local optima. With a single agent you have no way to know whether the peak you found is global. This system addresses the problem by:

1. Running four agents with **different starting waypoint sequences** that systematically cover different quadrants of the landscape.
2. Detecting local maxima via *oscillation detection* (the agent bounces above/below the peak) and switching to a gradient-descent escape phase.
3. Tracking found local maxima and **redirecting redundant agents** away from already-explored peaks using trajectory intersection detection.

---

## Technical Approach

### Search strategies

Each agent independently selects one of four gradient-based movement rules per timestep:

| Strategy | Description |
|---|---|
| **Gradient Ascent (GA)** | `x_new = x + α · ∂z/∂x` — standard steepest ascent |
| **Gradient Descent (GD)** | `x_new = x − α · ∂z/∂x` — used to escape local maxima by descending into a valley first |
| **Momentum GA (MGA)** | Accumulates a velocity vector `v ← β·v − α·∇z`; smooths oscillations on flat ridges |
| **Momentum GD (MGD)** | Same momentum formulation, descending direction |

Parameters `α` (learning rate) and `β` (momentum coefficient) are tuned per agent.

### Local-maxima detection and escape

While climbing (`strat = "hike"`), an agent monitors whether altitude *decreased* on the last step—a sign it overshot a peak. When this oscillation is observed twice in a row, the agent:

1. Approximates the local maximum as the midpoint between the last two positions.
2. Stores the coordinates in a shared `local_maxs` list.
3. Switches to `"descent"` mode to escape the basin.

The inverse logic applies during descent: two consecutive altitude *increases* signal a valley floor, so the agent switches back to `"hike"`.

### Agent coordination

At each iteration `check_hiker_intersect` projects the forward trajectory of every agent pair. If two agents on `"hike"` mode are heading toward the same point, the one *farther* from that point is redirected to a different waypoint, keeping agents spatially separated.

### Waypoint routing

Before gradient search begins, each agent navigates a predefined waypoint list designed to disperse the four agents across all four quadrants of the circular landscape (radius ≈ 23 000 units). Once the waypoints are exhausted the agent switches permanently to gradient search.

### Win detection

A `DataAnalyst` instance polls the server response for the `"cima": True` flag. When any agent reaches the global maximum, all agents navigate directly to the winning position to lock it in.

---

## Test Functions

The server supports the following optimization landscapes (selectable at startup):

| Function | Characteristics |
|---|---|
| **Ackley** | Many local optima, nearly flat outer region, sharp global maximum |
| **Rastrigin** | Highly multimodal, regular grid of local optima |
| **Easom** | Large flat region with a single narrow global maximum |
| **McCormick** | Non-convex with one global and several local minima |
| **Mishra Bird** | Constrained-looking landscape, steep gradients |
| **Sinusoidal** | Smooth periodic surface |
| **Easy** | Simple unimodal baseline for testing |

---

## Dashboard

A real-time **CustomTkinter** dashboard (`tpf_CLIFF_interface.py`) connects to the same server and visualises:

- **3D mountain surface** rendered with Matplotlib
- **Heatmap** of altitude values
- **ASCII art** representation
- **Scatter plot** of hiker positions over time
- **Leaderboard** showing current standings across all teams

Sample screenshots (dark and light themes):

| View | Dark | Light |
|---|---|---|
| Mountain | ![mountain dark](test_images/mountain_dark.png) | ![mountain light](test_images/mountain_light.png) |
| Heatmap | ![heatmap dark](test_images/heatmap_dark.png) | ![heatmap light](test_images/heatmap_light.png) |
| Hikers | ![hikers dark](test_images/hikers_dark.png) | ![hikers light](test_images/hikers_light.png) |

---

## Stack

| Layer | Technology |
|---|---|
| Language | Python 3.11 |
| Numerical computing | NumPy |
| Visualisation | Matplotlib, CustomTkinter |
| Image handling | Pillow (PIL) |
| Table rendering | PrettyTable, Tabulate |
| Networking | TCP sockets (stdlib) |

---

## Running Locally

```bash
# 1. Start the server (choose a landscape in start_local.py)
python start_local.py

# 2. Start the strategy client
python tpf_cliff_strat.py --ip 127.0.0.1:8080

# 3. (Optional) Launch the dashboard
python tpf_CLIFF_interface.py --ip 127.0.0.1:8080
```

Install dependencies:

```bash
pip install numpy matplotlib customtkinter Pillow prettytable tabulate
```

---

## Project Structure

```
.
├── tpf_cliff_strat.py           # Entry point — agent loop and coordination logic
├── tpf_CLIFF_interface.py       # Real-time dashboard (CustomTkinter)
├── tpf_CLIFF_interface_utils.py # Dashboard widgets
├── start_local.py               # Convenience launcher for local server
├── strategy/
│   ├── tpf_CLIFF_class_hiker.py       # Hiker agent (GA, GD, MGA, MGD, strategy FSM)
│   ├── tpf_CLIFF_class_dataAnalyst.py # Global state monitor
│   ├── tpf_CLIFF_constants.py          # Waypoint sequences per agent
│   └── tpf_CLIFF_intersection.py       # Geometry helpers (trajectory intersection)
├── communication/
│   ├── client/client.py         # TCP client wrapper
│   └── server/                  # Server code (provided by course)
│       └── mountain/            # Landscape implementations
└── classes/                     # Match, map, and circle helpers
```

---

## Notes

- The TCP server protocol and landscape implementations (`communication/server/`) were provided by the course. The search strategy, agent logic, coordination layer, and dashboard are original student work.
- Academic group project — Universidad de San Andrés, 2023.
