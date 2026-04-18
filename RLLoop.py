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

        self.steps += 1
        nxt = self.pos + (1 if action == 1 else -1)

        if 0 <= nxt < self.size:
            self.pos = nxt
            reward = 1.0 if self.pos == self.goal else -0.1
        else:
            reward = -0.5

        terminated = self.pos == self.goal
        truncated = self.steps >= self.max_steps and not terminated
        self.done = terminated or truncated

        return self.pos, reward, terminated, truncated


def policy(obs, goal):
    return 1 if obs < goal else 0   # move right until goal


env = LineWorld(size=5, max_steps=10)

obs = env.reset()
print(f"Start -> observation: {obs}")

while True:
    action = policy(obs, env.goal)
    next_obs, reward, terminated, truncated = env.step(action)

    print(
        f"action: {action} | "
        f"observation: {obs} -> next_observation: {next_obs} | "
        f"reward: {reward}"
    )

    obs = next_obs

    if terminated or truncated:
        print("Episode ended")
        break