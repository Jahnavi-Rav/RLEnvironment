# Toy RL Environment + Evaluation Harness

This project is a small Python-based learning project that combines three ideas:

1. a toy Reinforcement Learning (RL) environment  
2. a toy evaluation harness  
3. a toy benchmark design playground  

The goal is to understand, in a hands-on way, how agents interact with environments, how outputs are judged, and how benchmark design can fail if rewards or judges are not designed carefully.

---

# What this project covers

This repository demonstrates:

- a basic RL interaction loop  
- a simple LineWorld environment  
- a step-based reward system  
- a final pass/fail judge  
- a toy evaluation harness for code tasks  
- safe file checking and execution  
- benchmark edge cases such as:
  - benchmark too easy
  - benchmark impossible
  - reward too sparse
  - reward misaligned with real success
  - judge unintentionally rewarding shortcuts

---

# Core RL idea

The basic RL loop is:

```text
observation → action → reward → repeat
```

A more complete version is:

```text
observation → action → next observation → reward → repeat until done
```

This project uses that pattern in a simple form so the main concepts are easy to understand.

---

# LineWorld Environment

LineWorld is a very small 1D environment:

```text
0 → 1 → 2 → 3 → 4
```

- The agent starts at position `0`
- The goal is to reach position `4`
- The action space is:
  - `0` → move left
  - `1` → move right

This environment is intentionally simple so the focus stays on the RL loop and evaluation logic.

---

# How LineWorld works

## Environment state

The environment keeps track of:

- current position
- number of steps
- whether the episode is finished

## Step function

Each time the agent takes an action:

- the environment updates the position
- computes reward
- checks whether the episode ended
- returns the next observation

## Rewards

The toy setup uses:

- `+1` when the goal is reached
- `-0.1` for a normal step

This is an example of a mostly dense reward with a clear goal reward.

---

# RL Loop

The usual interaction pattern is:

1. observe current state  
2. choose an action  
3. apply action in the environment  
4. receive reward  
5. continue until the episode ends  

This is the main idea behind RL environments.

---

# Judge

This project also uses a simple final judge.

The final judge returns:

- `1.0` if the goal is reached
- `-1.0` otherwise

This is useful because it separates:
- step-level reward during interaction
- final evaluation at the end

---

# Static vs Interactive Evaluation

This project helps illustrate the difference between static and interactive evaluation.

## Static evaluation

A one-shot setup:

```text
input → model → output → judge
```

There is no interaction loop.

## Interactive evaluation

A multi-step setup:

```text
observation → action → feedback → repeat
```

The RL environment in this project is an example of interactive evaluation.

---

# One-shot vs Multi-step Tasks

## One-shot tasks

The model answers once.

Example:
- solve a direct question
- write a function once
- answer a multiple-choice question

## Multi-step tasks

The agent acts over time and may need multiple decisions.

Example:
- move through an environment
- debug code step by step
- interact with tools and update behavior

The RL part of this project is multi-step.

---

# Sparse Rewards vs Dense Rewards

## Sparse rewards

Reward comes only rarely, usually at the end.

Example:

```python
reward = 1.0 if success else 0.0
```

This is harder for learning because the agent gets very little feedback.

## Dense rewards

Reward is provided more often.

Example:

```python
reward = -0.1  # per step
reward += 1.0 if at_goal else 0.0
```

This gives the agent more guidance during the process.

The LineWorld example uses a simple dense-style step penalty plus a success reward.

---

# Offline Judge vs Online Judge

## Offline judge

Evaluation happens at the end.

Example:

```text
final output → judge → score
```

## Online judge

Evaluation happens during the process.

Example:

```text
step → reward → next step
```

This project demonstrates both ideas:
- online-style step rewards in the environment
- offline-style final scoring in the judge

---

# Evaluation Harness

This repository also includes a toy evaluation harness for code-based tasks.

The evaluation harness is designed to:

- check files
- read files safely
- load functions
- execute functions
- score outputs
- handle exceptions safely

A simple evaluation pipeline looks like this:

```text
file → load function → execute → judge → score
```

This is similar in spirit to how toy coding benchmarks or code evaluators work.

---

# What the evaluation harness checks

The harness can be used to simulate cases like:

- missing file
- malformed code
- wrong function name
- wrong function signature
- partial solution
- runtime crash
- timeout
- nondeterministic behavior

This helps show how judges and evaluators can distinguish different failure types.

---

# Scripts in the benchmark design section

The `BenchmarkDesign/` folder contains toy scripts that separate responsibilities.

## `checker.py`

Responsible for:
- checking whether a file exists
- reading file contents safely

## `executor.py`

Responsible for:
- loading a function from code
- executing a function safely
- catching execution errors

## `scorer.py`

Responsible for:
- comparing actual outputs with expected outputs
- assigning pass/fail
- assigning reward

## `main.py`

Responsible for:
- connecting all the steps together
- running the full evaluation pipeline

## `submission.py`

A simple example submission file used by the evaluator.

---

# Example submission

An example `submission.py` could look like this:

```python
def solve(x):
    return x + 1
```

This file is then checked, loaded, executed, and scored by the benchmark pipeline.

---

# Edge cases explored in this project

This project also includes toy examples of benchmark design problems.

## 1. Benchmark too easy

Example:

```python
output = agent.solve("2+2")
```

Problem:
- almost every reasonable agent passes
- benchmark does not distinguish strong agents from weak ones

## 2. Benchmark impossible

Example:

```python
output = agent.solve("guess hidden number")
```

Problem:
- no agent can solve it
- benchmark gives little useful signal

## 3. Reward too sparse

Example:

```python
reward = 1.0 if success else 0.0
```

Problem:
- the agent gets no guidance during intermediate steps

## 4. Reward misaligned with real success

Example:

```python
reward = len(output) / 100.0
```

Problem:
- the agent may optimize output length instead of correctness

## 5. Judge unintentionally rewards shortcuts

Example:

```python
if "PASS" in output:
    reward = 1.0
```

Problem:
- the agent can game the judge without solving the real task

These are important because benchmark quality matters just as much as agent quality.

---

# Example failure cases handled

The toy code paths discussed in this project include:

- agent outputs malformed files
- agent crashes midway
- agent creates correct-looking file with wrong function signature
- agent solves partially but not fully
- agent times out
- agent produces nondeterministic outputs

These help show how an evaluator can classify outcomes and assign different rewards instead of only returning a simple pass/fail.

---

# Why this project matters

This project is useful for understanding:

- how simple RL environments are structured
- how judges and evaluators work
- how benchmark design can go wrong
- how reward design affects agent behavior
- how safe execution and exception handling matter in evaluation systems

Even though the code is small, the ideas connect to larger systems used in:
- RL research
- agent evaluation
- coding benchmarks
- tool-using AI systems

---

# Project structure

```text
RLEnvironment/
│
├── Environment.py
├── RLLoop.py
├── EnvJudgement.py
├── EdgeCase.py
├── EvalHarness.py
├── README.md
├── .gitignore
│
└── BenchmarkDesign/
    ├── checker.py
    ├── executor.py
    ├── scorer.py
    ├── main.py
    └── submission.py
```

If your exact local structure differs slightly, this section can be adjusted to match it.

---

# How to run

## 1. Run the RL environment

```bash
python RLLoop.py
```

## 2. Run edge case simulation

```bash
python EdgeCase.py
```

## 3. Run the evaluation harness

```bash
python EvalHarness.py
```

## 4. Run the benchmark design pipeline

From the project root:

```bash
python BenchmarkDesign/main.py BenchmarkDesign/submission.py
```

If your `main.py` uses a default path, you can also run it without passing the file explicitly, depending on how your code is written.

---

# Example concepts demonstrated in code

This repository includes toy implementations related to:

- environment reset and step logic
- action → observation → reward loops
- pass/fail judges
- scalar reward judges
- code checking and execution
- safe exception handling
- evaluation summaries
- benchmark edge case simulation

---

# Possible future improvements

This project can be extended in many ways. Some useful next steps would be:

- add Q-learning
- add a random policy baseline
- add more realistic test cases
- use `ast.parse()` to detect malformed Python more properly
- check function signatures more robustly
- detect nondeterminism by running the same function multiple times
- add better summaries and metrics
- convert the environment to a Gym-style interface

---

# Who this is for

This project is useful for:
- beginners learning RL basics
- anyone trying to understand evaluation harnesses
- people preparing for AI/ML engineering interviews
- anyone interested in benchmark design and failure modes

---

# Summary

In short, this repository combines:

- a toy RL environment
- a toy judge
- a toy code evaluation harness
- a toy benchmark design simulator

The main purpose is educational: to make the ideas behind environments, rewards, judges, and evaluation systems easier to understand through small Python examples.

---

## Author

Jahnavi Ravi