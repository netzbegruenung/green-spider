FROM debian:stretch-slim

RUN apt-get update \
  && apt-get install -y git wget gnupg fonts-liberation libappindicator3-1 \
    libasound2 libatk-bridge2.0-0 libatk1.0-0 libcairo2 libcups2 libdbus-1-3 \
    libexpat1 libgdk-pixbuf2.0-0 libglib2.0-0 libgtk-3-0 libnspr4 libnss3 \
    libpango-1.0-0 libpangocairo-1.0-0 libx11-6 libx11-xcb1 libxcb1 \
    libxcomposite1 libxcursor1 libxdamage1 libxext6 libxfixes3 libxi6 \
    libxrandr2 libxrender1 libxss1 libxtst6 lsb-release xdg-utils \
    python3 python3-pip unzip \
  && apt-get clean \
  && wget https://dl.google.com/linux/direct/google-chrome-stable_current_amd64.deb \
    && dpkg -i google-chrome-stable_current_amd64.deb \
    && rm google-chrome-stable_current_amd64.deb \
  && pip3 install GitPython idna PyYAML beautifulsoup4==4.6.0 requests==2.18.4 responses==0.9.0 selenium==3.11.0 smmap2==2.0.3 urllib3==1.22 certifi==2018.1.18 \
  && wget https://chromedriver.storage.googleapis.com/2.38/chromedriver_linux64.zip \
    && unzip chromedriver_linux64.zip \
    && rm chromedriver_linux64.zip \
  && apt-get clean

RUN wget https://bitbucket.org/ariya/phantomjs/downloads/phantomjs-2.1.1-linux-x86_64.tar.bz2 \
    && tar xjf phantomjs-2.1.1-linux-x86_64.tar.bz2 \
    && mv phantomjs-2.1.1-linux-x86_64/bin/phantomjs /usr/local/bin/ \
    && rm -rf phantomjs-2.1.1-linux-x86_64

ADD spider.py /
ADD spider_test.py /

ENTRYPOINT ["python3"]
CMD ["/spider.py"]
