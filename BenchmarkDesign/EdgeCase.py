class ToyBenchmark:
    def __init__(self, mode):
        self.mode = mode

    def evaluate(self, agent):
        if self.mode == "too_easy":
            output = agent.solve("2+2")
            return {"status": "pass" if output == "4" else "fail", "reward": 1.0 if output == "4" else 0.0}

        if self.mode == "impossible":
            output = agent.solve("guess hidden number")
            return {"status": "fail", "reward": 0.0}

        if self.mode == "reward_too_sparse":
            output = agent.solve("multi_step_task")
            success = output == "final_correct"
            return {"status": "pass" if success else "fail", "reward": 1.0 if success else 0.0}

        if self.mode == "misaligned_reward":
            output = agent.solve("write fast code")
            reward = len(output) / 100.0   # bad reward: longer output gets more reward
            success = output == "correct_solution"
            return {"status": "pass" if success else "fail", "reward": reward}

        if self.mode == "shortcut_reward":
            output = agent.solve("solve securely")
            if "PASS" in output:   # bad judge: rewards fake success text
                return {"status": "pass", "reward": 1.0}
            return {"status": "fail", "reward": 0.0}


class ToyAgent:
    def __init__(self, behavior):
        self.behavior = behavior

    def solve(self, task):
        if self.behavior == "honest":
            if task == "2+2":
                return "4"
            if task == "multi_step_task":
                return "partial_work"
            if task == "write fast code":
                return "correct_solution"
            if task == "solve securely":
                return "real_secure_solution"
            return "unknown"

        if self.behavior == "shortcut":
            if task == "solve securely":
                return "PASS"
            if task == "write fast code":
                return "x" * 500
            return "wrong"

        return "wrong"


modes = [
    "too_easy",
    "impossible",
    "reward_too_sparse",
    "misaligned_reward",
    "shortcut_reward",
]

agents = [ToyAgent("honest"), ToyAgent("shortcut")]

for mode in modes:
    print(f"\n--- Benchmark mode: {mode} ---")
    bench = ToyBenchmark(mode)
    for agent in agents:
        result = bench.evaluate(agent)
        print(agent.behavior, "->", result)