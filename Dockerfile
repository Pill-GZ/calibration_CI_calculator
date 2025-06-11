FROM python:3.10-slim

# ARG AWSACCOUNT
# ARG S3BUCKET

# ENV AWS_ACCOUNT=$AWSACCOUNT
# ENV S3_BUCKET=$S3BUCKET

WORKDIR /app

# RUN apt-get update && apt-get install -y \
#     build-essential \
#     curl \
#     software-properties-common \
#     git \
#     && rm -rf /var/lib/apt/lists/*

WORKDIR /home/app

COPY app.py .
COPY about.py .
COPY constants.py .
COPY stats.py .
COPY requirements.txt .

RUN pip3 install --no-cache-dir --upgrade -r requirements.txt

EXPOSE 3838

HEALTHCHECK CMD curl --fail http://localhost:3838/_stcore/health

CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "3838"]


# I was able to build and run with the following commands:
# sudo docker build -t ci-ote-app-test .
# sudo docker run -p 3838:3838 ci-ote-app-test