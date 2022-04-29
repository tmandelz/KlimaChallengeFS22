FROM python:3.9-slim as base

# Update base container install
RUN apt-get update && apt-get install -y --no-install-recommends gcc && apt-get install gdal-bin -y
RUN pip install --upgrade pip

COPY requirements.txt /tmp/
RUN pip install --requirement /tmp/requirements.txt
COPY . /tmp/

# Setup env
ENV LANG C.UTF-8
ENV LC_ALL C.UTF-8
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONFAULTHANDLER 1

FROM base AS runtime
# Create and switch to a new user
RUN useradd --create-home appuser
WORKDIR /home/appuser
USER appuser

# Install application into container
COPY . .

# Run the application
ENTRYPOINT ["python", "-m", "http.server"]
CMD ["--directory", "klima", "8000"]