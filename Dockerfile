# 1) choose base container
# generally use the most recent tag

# data science notebook
# https://hub.docker.com/repository/docker/ucsdets/datascience-notebook/tags
ARG BASE_CONTAINER=ucsdets/datascience-notebook:2020.2-stable

# scipy/machine learning (tensorflow)
# https://hub.docker.com/repository/docker/ucsdets/scipy-ml-notebook/tags
# ARG BASE_CONTAINER=ucsdets/scipy-ml-notebook:2020.2-stable

FROM $BASE_CONTAINER

LABEL maintainer="UC San Diego ITS/ETS <ets-consult@ucsd.edu>"

# 2) change to root to install packages
USER root

RUN	apt-get install htop

# 3) install packages
RUN pip install --no-cache-dir implicit
RUN pip install --no-cache-dir Cython  
RUN pip install --no-cache-dir Keras Keras-Applications Keras-Preprocessing
RUN pip install --no-cache-dir dm-sonnet
RUN pip install --no-cache-dir h5py
RUN pip install --no-cache-dir nose
RUN pip install --no-cache-dir numpy
RUN pip install --no-cache-dir pandas
RUN pip install --no-cache-dir scikit-learn scikit-optimize
RUN pip install --no-cache-dir scipy
RUN pip install --no-cache-dir seaborn
# Tensorflow packages
RUN pip install --no-cache-dir tensorboard tensorflow tensorflow-estimator tensorflow-probability
RUN pip install --no-cache-dir tqdm
RUN pip install --no-cache-dir wrapt








# # 4) change back to notebook user
# COPY /run_jupyter.sh /
# USER $NB_UID

# Override command to disable running jupyter notebook at launch
# CMD ["/bin/bash"]