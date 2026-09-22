FROM python:3.14-slim

RUN apt-get update \
    && apt-get install -y --no-install-recommends build-essential \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

RUN useradd --system --create-home --shell /usr/sbin/nologin appuser \
    && chown -R appuser:appuser /app
USER appuser

EXPOSE 5000

# FLASK_SECRET_KEY must be set at runtime: uwsgi.ini runs multiple worker
# processes, and without a fixed key each process would sign session
# cookies differently, breaking logins at random depending which worker
# handles a request.
CMD ["uwsgi", "--ini", "uwsgi.ini"]
