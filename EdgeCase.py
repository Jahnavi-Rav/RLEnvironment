import random


class ToyTaskEnv:
    def __init__(self, max_steps=5):
        self.max_steps = max_steps
        self.reset()

    def reset(self):
        self.steps = 0
        self.done = False
        return {"task": "Create solve(x) that returns x + 1"}

    def step(self, agent_output):
        if self.done:
            raise RuntimeError("Episode already ended")

        self.steps += 1
        reward, result = judge(agent_output, self.steps, self.max_steps)

        terminated = result in {"pass", "malformed", "crash", "wrong_signature", "partial", "nondeterministic"}
        truncated = self.steps >= self.max_steps and result == "timeout"
        self.done = terminated or truncated

        obs = {"judge_result": result, "steps": self.steps}
        return obs, reward, terminated, truncated


def run_agent_case(case_name):
    if case_name == "malformed":
        return {"file_content": "def solve(x)\n return x+1"}   # broken syntax

    if case_name == "crash":
        raise RuntimeError("Agent crashed midway")

    if case_name == "wrong_signature":
        return {"file_content": "def solve(a, b):\n    return a + 1"}

    if case_name == "partial":
        return {"file_content": "def solve(x):\n    return x"}   # incomplete

    if case_name == "timeout":
        return None

    if case_name == "nondeterministic":
        val = random.randint(0, 1)
        return {"file_content": f"def solve(x):\n    return x + {val}"}

    if case_name == "pass":
        return {"file_content": "def solve(x):\n    return x + 1"}


def judge(agent_output, step_num, max_steps):
    if agent_output is None:
        return (-1.0, "timeout") if step_num >= max_steps else (-0.2, "timeout")

    file_content = agent_output.get("file_content", "")

    if "def solve(x)\n" in file_content:
        return -1.0, "malformed"

    if "def solve(a, b)" in file_content:
        return -0.8, "wrong_signature"

    if "return x\n" in file_content:
        return -0.5, "partial"

    if "return x + 0" in file_content or "return x + 1" in file_content:
        if "return x + 0" in file_content:
            return -0.9, "nondeterministic"
        return 1.0, "pass"

    return -1.0, "malformed"


# -------- Simulation --------
cases = ["malformed", "wrong_signature", "partial", "timeout", "nondeterministic", "pass"]

for case in cases:
    print(f"\n--- Case: {case} ---")
    env = ToyTaskEnv(max_steps=3)
    obs = env.reset()
    print("Initial observation:", obs)

    terminated = truncated = False

    while not (terminated or truncated):
        try:
            output = run_agent_case(case)
        except Exception:
            output = {"file_content": "AGENT_CRASH"}
            reward, result = -1.0, "crash"
            print({"judge_result": result, "reward": reward})
            break

        obs, reward, terminated, truncated = env.step(output)
        print({"judge_result": obs["judge_result"], "reward": reward})

        if case != "timeout":
            break