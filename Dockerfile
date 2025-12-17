FROM python:3.13-slim-bookworm

# Accept version as build argument
ARG VERSION=unknown

# No additional system dependencies needed for production

# Install things needed for the bot - order IS important
COPY ./src/requirements.txt /tmp/requirements.txt
RUN pip install --no-cache-dir --break-system-packages -r /tmp/requirements.txt

# Create bot user
RUN useradd -m -s /bin/bash zulip-bot
WORKDIR /home/zulip-bot
COPY --chown=zulip-bot:zulip-bot ./src/ ./

# Update version.py with build-time version
RUN sed -i "s/__version__ = \".*\"/__version__ = \"${VERSION}\"/" /home/zulip-bot/version.py

USER zulip-bot

# Set version environment variable (can be overridden at runtime)
ENV RITSUKO_VERSION="${VERSION}"

CMD ["python3", "bot.py"]
