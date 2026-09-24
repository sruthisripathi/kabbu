# Kabbu

A small two-legged messenger robot that understands Telugu, English and code-mixed commands, runs compressed models on-device (ESP32-S3), and answers to its name.

## Structure
- `firmware/` – main robot firmware (XIAO ESP32S3)
- `face/` – face controller firmware (ESP32-C3)
- `sim/` – MuJoCo model and RL walking training
- `ml/` – language model, wake word and perception pipelines
- `app/` – phone web app
- `hardware/` – wiring diagrams, measurements, 3D models
- `docs/` – build log and results

## Setup
- WSL 2 Ubuntu, Python venv in `sim/.venv`
- PyTorch (CUDA 13.0 build), MuJoCo, Gymnasium, Stable-Baselines3
