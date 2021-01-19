FROM python

RUN pip install python-telegram-bot requests
WORKDIR /bot
COPY infn_jobs_bot.py /bot

CMD python -u infn_jobs_bot.py