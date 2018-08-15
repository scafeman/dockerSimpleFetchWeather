FROM python:3.4-alpine
ADD . /web
WORKDIR /web
RUN pip install --proxy https://wp.de.eld.ericsson.se:3128 --trusted-host pypi.python.org -r requirements.txt
EXPOSE 80

# set environment variable so that python does not buffer any output logs
ENV PYTHONUNBUFFERED 0
CMD ["python", "index.py"]
