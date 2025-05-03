import torch

def save_model(model, path):
    torch.save(model.state_dict(), path)
    print(f"Model saved at {path}")

def load_model(model, path):
    model.load_state_dict(torch.load(path))
    model.eval()
    print(f"Model loaded from {path}")