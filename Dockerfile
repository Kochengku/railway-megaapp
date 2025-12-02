FROM python:3.11-slim

# Install MEGAcmd
RUN apt-get update && apt-get install -y \
    wget \
    curl \
    gnupg \
    ca-certificates \
    && wget https://mega.nz/linux/repo/Debian_11/amd64/megacmd-Debian_11_amd64.deb \
    && apt install -y ./megacmd-Debian_11_amd64.deb \
    && rm -f megacmd-Debian_11_amd64.deb

WORKDIR /app

COPY requirements.txt requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

ENV PORT=8000

CMD ["python", "app.py"]