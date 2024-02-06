FROM python:3.9

RUN pip install python-telegram-bot==13 requests urllib3
WORKDIR /bot
COPY infn_jobs_bot.py /bot

CMD python -u infn_jobs_bot.py