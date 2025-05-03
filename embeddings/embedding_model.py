# models/embedding_model.py

import torch
import torch.nn as nn
from torchvision import models, transforms

class EmbeddingModel(nn.Module):
    def __init__(self, device='cuda' if torch.cuda.is_available() else 'cpu'):
        super(EmbeddingModel, self).__init__()

        # Load pretrained ResNet50
        resnet = models.resnet50(pretrained=True)

        # Remove the final classification layer (fc)
        self.backbone = nn.Sequential(*list(resnet.children())[:-1])  # [:-1] removes the FC layer

        # Freeze all layers (optional)
        for param in self.backbone.parameters():
            param.requires_grad = False

        self.device = device
        self.to(device)

    def forward(self, x):
        x = self.backbone(x)          # Shape: (batch_size, 2048, 1, 1)
        x = x.view(x.size(0), -1)     # Shape: (batch_size, 2048)
        return x
