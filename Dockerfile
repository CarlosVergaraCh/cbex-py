FROM python:3.10
 
# Creating Application Source Code Directory
RUN mkdir -p /cbex-py
# Setting Home Directory for containers
WORKDIR /cbex-py
# Copying src code to Container
COPY . /cbex-py/
# Installing openssl
RUN apt-get update
RUN apt-get install -y build-essential cmake zlib1g-dev libcppunit-dev git subversion wget && rm -rf /var/lib/apt/lists/*
RUN wget https://www.openssl.org/source/openssl-1.1.1v.tar.gz -O - | tar -xz
RUN echo 'export PATH="/usr/local/opt/openssl@1.1/bin:$PATH"' >> ~/.zshrc
RUN export LDFLAGS="-L/usr/local/opt/openssl@1.1/lib"
RUN export CPPFLAGS="-I/usr/local/opt/openssl@1.1/include"
# Installing python dependencies
RUN python -m pip install --upgrade pip setuptools wheel
RUN pip install -r requirements.txt
# Exposing Ports
EXPOSE 5000
# Cleaningup data
# RUN python cleanup.py
# Loading data
# RUN python create_dataset.py
# Running Python Application
CMD [“python”, “app.py”]
