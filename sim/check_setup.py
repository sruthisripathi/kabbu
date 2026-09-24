import torch, mujoco, gymnasium as gym

print("PyTorch:", torch.__version__)
print("CUDA available:", torch.cuda.is_available())
if torch.cuda.is_available():
    print("GPU:", torch.cuda.get_device_name(0))

print("MuJoCo:", mujoco.__version__)

env = gym.make("Humanoid-v5", render_mode="human")
obs, _ = env.reset(seed=0)
for _ in range(500):
    obs, reward, terminated, truncated, _ = env.step(env.action_space.sample())
    if terminated or truncated:
        obs, _ = env.reset()
env.close()
print("Humanoid sim ran OK")