FROM python:3.14-slim

RUN apt-get update \
    && apt-get install -y --no-install-recommends build-essential \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Fixed numeric uid/gid: Kubernetes' runAsNonRoot check can only verify a
# named user by resolving it against the pod's securityContext.runAsUser -
# it can't run the image to look it up, so USER must be numeric here.
RUN groupadd --gid 1000 appuser \
    && useradd --uid 1000 --gid 1000 --create-home --shell /usr/sbin/nologin appuser \
    && chown -R appuser:appuser /app
USER 1000:1000

EXPOSE 5000

# FLASK_SECRET_KEY must be set at runtime: uwsgi.ini runs multiple worker
# processes, and without a fixed key each process would sign session
# cookies differently, breaking logins at random depending which worker
# handles a request.
CMD ["uwsgi", "--ini", "uwsgi.ini"]
