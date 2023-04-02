FROM python:3.10-slim-bullseye

# Copy code and requirements
COPY ./requirements.txt /opt/app/
COPY ./app.py /opt/app/
COPY .appenv /opt/app/

# Install requirements
RUN pip install -r /opt/app/requirements.txt

# Set app workdir
WORKDIR /opt/app

# Set entrypoint
ENTRYPOINT ["python", "app.py"]