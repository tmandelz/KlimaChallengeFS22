FROM python:3.9-slim as base

# Update base container install
RUN apt-get update && apt-get install -y --no-install-recommends gcc && apt-get install gdal-bin -y && apt-get install nano
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
WORKDIR /klima/

EXPOSE 8050
EXPOSE 80
EXPOSE 443


# Install application into container
COPY . .


# Run the application
# CMD python Datapipeline.py
# CMD gunicorn DashboardServer:server --bind 172.28.1.5:8050
ENTRYPOINT ["python", "-m", "http.server"]
CMD ["--directory", "directory", "8000"]
