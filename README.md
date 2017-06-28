# IFFSE
## Facial Feature Search Engine for some Photo Sharing Website

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

# Annoy Issue:
# Annoy uses libstdc++, Anaconda provides its own libstdc++,
# to use annoy in Anaconda, run:
cp /usr/lib/x86_64-linux-gnu/libstdc++.so.6 $CONDA_PATH/envs/facemaps/lib 
```

### Dependencies:
```bash
conda install -c conda-forge dlib=19.4
conda install pytorch torchvision -c soumith
pip install -r requirements.txt
```

# Deploying a local copy
1. Before anything, you'll need to download a copy of the pretrained weights:
```bash
git clone https://github.com/kendricktan/iffse.git
cd iffse
mkdir pretrained_weights
wget https://github.com/ageitgey/face_recognition_models/raw/master/face_recognition_models/models/shape_predictor_68_face_landmarks.dat -O ./pretrained_weights/shape_predictor_68_face_landmarks.dat
wget https://www.dropbox.com/s/lhus56cn1xikzeb/openface_cpu.pth?dl=1 -O ./pretrained_weights/openface_cpu.pth
```

2. Time to scrap some data! I've written async multi-threaded scrapper that __doesn't__ require any instagram credentials :-). The following tags are used int `scrapper.py`, change them to whatever tags you want to scrap (e.g. `#NYC`, `#gymlife`)
```python
# What kind of tags do we want to scrap
tags_to_be_scraped = [
    'selfie', 'selfportait', 'dailylook', 'selfiesunday',
    'selfietime', 'instaselfie', 'shamelessselefie',
    'faceoftheday', 'me', 'selfieoftheday', 'instame',
    'selfiestick', 'selfies'
]
```

2. Run `python scrapper.py` and wait for a few hours / days. Ideally you do this step on a `C4 instance` on AWS as it'll max out your cores.

3. Run server

```bash
# If you're running it for the first time
# or want to update search indexes
python app.py --rebuild-tree

# Otherwise
python app.py
```

# Special thanks:
[OpenFacePytorch](https://github.com/thnkim/OpenFacePytorch) - OpenFace's `nn4.small2.v1.t7` model in PyTorch
