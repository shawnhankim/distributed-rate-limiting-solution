FROM python:3.7
LABEL maintainer="Shawn"

COPY ./services/rate-limiter/. /var/www/rate-limiter/

WORKDIR /var/www/rate-limiter/app
ENV PYTHONPATH "${PYTHONPATH}:/var/www/rate-limiter/"

RUN pip install -r requirements.txt

ENTRYPOINT ["python"]
CMD ["app.py"]
