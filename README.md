# facemaps
Reverse face search for (public) instagram users

# Setup
The recommended way of installing a local copy of facemaps is to use a python 3.6 conda environment:

```bash
wget https://repo.continuum.io/miniconda/Miniconda3-latest-Linux-x86_64.sh -O conda.sh
chmod +x conda.sh
bash conda.sh
source ~/.bashrc # or `source ~/.zshrc` if you're using zsh

# Create new conda env and use it
conda create -n facemaps python=3.6 anaconda
source activate facemaps
```

### Dependencies:
```
conda install -c menpo dlib=19.4
conda install pytorch torchvision -c soumith
pip install -r requirements.txt
```

# Special thanks:
[OpenFacePytorch](https://github.com/thnkim/OpenFacePytorch) - PyTorch module to use OpenFace's `nn4.small2.v1.t7` model
