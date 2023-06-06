FROM python:3.9.13

RUN pip install pandas 
RUN pip install boto3
RUN pip install oss2
RUN pip install redis
RUN pip install numpy
RUN pip install pymongo
RUN pip install pika
RUN pip install docker
RUN pip install pyyaml
RUN pip install tqdm 
RUN pip install tablib
RUN pip install trading_calendars
RUN pip install xmltodict
RUN pip install simplejson
RUN pip install alpaca_trade_api 
RUN pip install python-telegram-bot
RUN pip install influxdb_client
#RUN pip install MetaTrader5
RUN pip install ta
RUN pip install binance-futures-connector==4.0.0rc2

### This one is the base image for installing relevenat building tools
ENV TZ=America/New_York
RUN ln -snf /usr/share/zoneinfo/$TZ /etc/localtime && echo $TZ > /etc/timezone

WORKDIR /home/xtraderbacktest

COPY ./ /home/xtraderbacktest/

WORKDIR /home/xtraderbacktest/modules/broker/
ENTRYPOINT  ["python3"] 

## sudo docker rmi xtbbroker; sudo docker build -f DockerFile . -t xtbbroker;
## run docker image
## docker run -d -it --net=host --rm --name xtbbroker-binance_x xtbbroker ./binance_x/binance_x.py <symbol>