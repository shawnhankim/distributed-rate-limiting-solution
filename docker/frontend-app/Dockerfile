FROM nginx

LABEL maintainer="Shawn"

RUN   mkdir -p /etc/nginx
RUN   mkdir -p /etc/nginx/conf.d
RUN   chmod -R 777 /etc/nginx
RUN   chmod -R 777 /etc/nginx/conf.d
RUN   chmod -R 777 /usr/share/nginx/html/

COPY  ./services/frontend-app    /etc/nginx/

STOPSIGNAL SIGTERM
CMD ["nginx", "-g", "daemon off;"]
