FROM python:3.12-bullseye

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# Set work directory
WORKDIR /home/app

# Install dependencies
COPY requirements.txt /home/app/requirements.txt
RUN pip install --upgrade pip
RUN pip install -r /home/app/requirements.txt
RUN pip install daphne


# Copy project
COPY . /home/app

RUN python manage.py collectstatic --no-input

CMD ["daphne", "-b", "0.0.0.0", "-p", "8000", "store.asgi:application"]
