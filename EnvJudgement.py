class LineWorld:
    def __init__(self, size=5, max_steps=10):
        self.size = size
        self.goal = size - 1
        self.max_steps = max_steps
        self.reset()

    def reset(self):
        self.pos = 0
        self.steps = 0
        self.done = False
        return self.pos

    def step(self, action):
        if self.done:
            raise RuntimeError("Reset first")

        self.steps += 1

        # move: 1 = right, 0 = left
        move = 1 if action == 1 else -1
        new_pos = self.pos + move

        # check boundaries
        if 0 <= new_pos < self.size:
            self.pos = new_pos

        # reward from environment (basic)
        reward = 1 if self.pos == self.goal else -0.1

        terminated = self.pos == self.goal
        truncated = self.steps >= self.max_steps and not terminated
        self.done = terminated or truncated

        return self.pos, reward, terminated, truncated


# -------- Judge --------
def judge(obs, goal, steps):
    if obs == goal:
        return 1.0      # success
    return -1.0         # failure


# -------- Simulation Loop --------
env = LineWorld()
obs = env.reset()

while not env.done:
    action = 1 if obs < env.goal else 0   # simple policy
    obs, reward, terminated, truncated = env.step(action)
    print(f"obs={obs}, reward={reward}")

# final judgment
score = judge(obs, env.goal, env.steps)
print("Final Score:", score)