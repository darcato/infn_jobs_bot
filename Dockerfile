FROM python

RUN pip install python-telegram-bot beautifulsoup4 requests
WORKDIR /bot
COPY infn_jobs_bot.py /bot

CMD python -u infn_jobs_bot.py