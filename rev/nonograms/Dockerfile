FROM nginx:latest

COPY nonograms_v4.tar /tmp/nonograms.tar
RUN mkdir -p /usr/share/nginx/html && \
    tar -xf /tmp/nonograms.tar --strip-components 1 -C /usr/share/nginx/html
