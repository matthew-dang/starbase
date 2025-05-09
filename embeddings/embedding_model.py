import torch
import torch.nn as nn
from torchvision import models, transforms

class EmbeddingModel(nn.Module):
    def __init__(self, device='cuda' if torch.cuda.is_available() else 'cpu'):
        super(EmbeddingModel, self).__init__()

        resnet = models.resnet50(pretrained=True)

        self.backbone = nn.Sequential(*list(resnet.children())[:-1])

        for param in self.backbone.parameters():
            param.requires_grad = False

        self.device = device
        self.to(device)

    def forward(self, x):
        x = self.backbone(x)
        x = x.view(x.size(0), -1) 
        return x
