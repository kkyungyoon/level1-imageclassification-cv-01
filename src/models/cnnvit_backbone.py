import torch.nn as nn
import torch
import torchvision.models as models
from torchvision.models import vit_b_16

import math

class PatchEmbedding(nn.Module):
    def __init__(self, img_size=224, patch_size=16, in_chans=3, embed_dim=768):
        super().__init__()
        self.img_size = img_size
        self.patch_size = patch_size
        self.n_patches = (img_size // patch_size) ** 2

        self.proj = nn.Conv2d(in_chans, embed_dim, kernel_size=patch_size, stride=patch_size)

    def forward(self, x):
        x = self.proj(x)  # (batch_size, embed_dim, n_patches ** 0.5, n_patches ** 0.5)
        x = x.flatten(2)  # (batch_size, embed_dim, n_patches)
        x = x.transpose(1, 2)  # (batch_size, n_patches, embed_dim)
        return x

class CNNViTModel(nn.Module):
    def __init__(self, num_cnn_classes, num_classes, pretrained):
        super(CNNViTModel, self).__init__()
        
        # CNN 부분 (ResNet50, resnext50_32x4d 등)
        self.cnn_model = models.resnext50_32x4d(pretrained=pretrained)
        self.cnn_model.fc = nn.Linear(self.cnn_model.fc.in_features, num_cnn_classes)

        self.pos_embed = self.create_sincos_positional_embedding(
            (224 // 16)**2 + 1, 768
        )
        self.patch_embed = PatchEmbedding()

        self.vit = vit_b_16(pretrained=pretrained)
        self.vit_encoder = self.vit.encoder

        self.linear_layer = nn.Linear(num_cnn_classes, 768)

        self.vit.heads = nn.Linear(768, num_classes)

    def create_sincos_positional_embedding(self, n_positions, dim):
        position = torch.arange(n_positions).unsqueeze(1)
        div_term = torch.exp(torch.arange(0, dim, 2) * -(math.log(10000.0) / dim))
        pe = torch.zeros(n_positions, dim)
        pe[:, 0::2] = torch.sin(position * div_term)
        pe[:, 1::2] = torch.cos(position * div_term)
        return nn.Parameter(pe.unsqueeze(0), requires_grad=False)

    def forward(self, x):
        # CNN
        cnn_logits = self.cnn_model(x)
        
        # cls_token_embedding
        cls_token_embedding = self.linear_layer(cnn_logits)

        # PatchEmbedding
        vit_input = self.patch_embed(x)

        cls_token = cls_token_embedding.unsqueeze(1)
        vit_input = torch.cat([cls_token, vit_input], dim=1)
        vit_input += self.pos_embed

        out = self.vit_encoder(vit_input)

        logits = self.vit.heads(out[:, 0])

        return logits