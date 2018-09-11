FROM debian:stretch-slim

RUN apt-get update \
  && apt-get install -y git wget gnupg fonts-liberation libappindicator3-1 \
    libasound2 libatk-bridge2.0-0 libatk1.0-0 libcairo2 libcups2 libdbus-1-3 \
    libexpat1 libgdk-pixbuf2.0-0 libglib2.0-0 libgtk-3-0 libnspr4 libnss3 \
    libpango-1.0-0 libpangocairo-1.0-0 libx11-6 libx11-xcb1 libxcb1 \
    libxcomposite1 libxcursor1 libxdamage1 libxext6 libxfixes3 libxi6 \
    libxrandr2 libxrender1 libxss1 libxtst6 lsb-release xdg-utils \
    python3 python3-pip unzip chromium-driver \
  && apt-get clean \
  && pip3 install GitPython idna PyYAML beautifulsoup4==4.6.0 requests==2.18.4 responses==0.9.0 selenium==3.14.0 smmap2==2.0.3 urllib3==1.22 google-cloud-datastore==1.7.0 tenacity==5.0.2 \
  && apt-get clean

ADD spider.py /
ADD spider_test.py /
ADD data_export.py /

ENTRYPOINT ["python3"]
CMD ["/spider.py"]
