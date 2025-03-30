FROM python:slim-bullseye AS app

FROM pwn.red/jail
COPY --from=app / /srv
COPY server.py /srv/app/run
COPY hamiltonicity.py flag.txt /srv/app/
ENV JAIL_TIME=600 JAIL_MEM=20M JAIL_CPU=500