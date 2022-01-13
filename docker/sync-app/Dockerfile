FROM python:3.7
LABEL maintainer="Shawn"

COPY ./services/sync-app/. /var/www/sync-app/

WORKDIR /var/www/sync-app/app
ENV PYTHONPATH "${PYTHONPATH}:/var/www/sync-app/"

RUN pip3 install -r requirements.txt

ENTRYPOINT ["python"]
CMD ["app.py"]
