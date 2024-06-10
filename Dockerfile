FROM python:latest

WORKDIR /usr/src/kraioko

SHELL ["/bin/bash", "-c"]

COPY . .
RUN python3 -m venv ./.venv
RUN source .venv/bin/activate
RUN python3 -m pip install --no-cache-dir -r ./req.txt

VOLUME /usr/src/kraioko/db

CMD ["python3", "./bot.py"]
