FROM python:3.5.3-alpine
COPY docker-entrypoint.sh /docker-entrypoint.sh
COPY requirements.txt /requirements.txt
RUN pip install -r /requirements.txt
ADD . /project
WORKDIR /project
RUN ["python", "manage.py", "migrate"]

CMD ["/docker-entrypoint.sh"]