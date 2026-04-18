# Toy RL Environment – LineWorld

This is a very simple Reinforcement Learning (RL) environment built in Python.

The goal of this project is to understand how the basic RL loop works:
**observation → action → reward → repeat**

---

## What is LineWorld?

LineWorld is a 1D environment:

0 → 1 → 2 → 3 → 4

- The agent starts at position `0`
- The goal is to reach position `4`
- The agent can move:
  - `0` → left
  - `1` → right

---

## How it works

### Environment
- Keeps track of:
  - current position
  - number of steps
  - whether the episode is finished

### Step function
Each step:
- Moves the agent
- Updates position
- Returns:
  - new observation (position)
  - reward
  - whether episode ended

### Rewards
- `+1` → if goal is reached  
- `-0.1` → for normal steps  

---

## RL Loop

The main loop follows this pattern:

1. Observe current position  
2. Choose action  
3. Take step in environment  
4. Get reward  
5. Repeat until done  

---

## Judge

A simple judge is used at the end:

- Returns `1.0` if goal is reached  
- Returns `-1.0` otherwise  

---

## How to run

```bash
python main.py