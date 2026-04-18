class LineWorld:
    def __init__(self, size=5, max_steps=20):
        self.size = size
        self.max_steps = max_steps
        self.goal = size - 1
        self.reset()

    def reset(self):
        self.pos = 0
        self.steps = 0
        self.done = False
        return self.pos

    def step(self, action):
        if self.done:
            raise RuntimeError("Episode is done. Call reset().")
        if action not in (0, 1):
            raise ValueError("Use 0 for left, 1 for right.")

        self.steps += 1
        new_pos = self.pos + (1 if action == 1 else -1)

        if new_pos < 0 or new_pos >= self.size:
            reward = -0.5
        else:
            self.pos = new_pos
            reward = 1.0 if self.pos == self.goal else -0.1

        terminated = self.pos == self.goal
        truncated = self.steps >= self.max_steps and not terminated
        self.done = terminated or truncated

        return self.pos, reward, terminated, truncated

    def render(self):
        print(" ".join("A" if i == self.pos else "G" if i == self.goal else "-" for i in range(self.size)))