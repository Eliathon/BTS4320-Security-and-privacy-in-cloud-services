FROM alpine
RUN apk add busybox-extras 
COPY index.html crypto.js var/www/
EXPOSE 80
CMD httpd -p 80 -h /var/www -f -vv
