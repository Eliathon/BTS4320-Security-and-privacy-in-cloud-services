FROM alpine
RUN apk add busybox-extras curl openssl
COPY index.cgi var/www/cgi-bin/
RUN chmod +x var/www/cgi-bin/index.cgi
EXPOSE 81
CMD httpd -p 81 -h /var/www -f -vv