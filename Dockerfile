FROM python:3.13-slim-bookworm

# Install system dependencies
#RUN apt-get update && \
#    apt-get install -y --no-install-recommends \
#        python3 \
#	 python3.13-venv \
#        python3-pip \
#        wget && \
#    apt-get clean && \
#    rm -rf /var/lib/apt/lists/*

# Install things needed for the bot - order IS important
COPY ./src/requirements.txt ./requirements.txt
RUN pip install --no-cache-dir --break-system-packages -r requirements.txt

# Create bot user
RUN useradd -m -s /bin/bash zulip-bot
WORKDIR /home/zulip-bot
COPY --chown=zulip-bot:zulip-bot ./src/ ./
USER zulip-bot

CMD ["zulip-run-bot", "bot.py", "--config-file", "zuliprc"]
