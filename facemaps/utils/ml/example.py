import torch

from torch.autograd import Variable
from loadOpenFace import prepareOpenFace

net = prepareOpenFace(useCuda=False).eval()
feature = net(Variable(torch.randn(1, 3, 96, 96)))
print(feature[0])
