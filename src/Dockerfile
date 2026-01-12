FROM python:3.13

LABEL maintainer="osipchuk.ls@phystech.edu" 
WORKDIR /app
ENV PIP_ROOT_USER_ACTION=ignore

COPY requirements.txt /app
RUN pip install -r requirements.txt

COPY ./ /app

ENTRYPOINT ["python3"]
CMD ["main.py"]
