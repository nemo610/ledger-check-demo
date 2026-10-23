FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1
WORKDIR /app
COPY agent_economy ./agent_economy
CMD ["python", "-m", "agent_economy.monitor"]
