FROM httpd:2.4
 
COPY ./artifacts/ /usr/local/apache2/htdocs/

EXPOSE 80