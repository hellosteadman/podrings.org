FROM python:3.11

# Install app
ADD requirements.txt /code/
WORKDIR /code
RUN pip install --no-cache-dir -qr /code/requirements.txt
COPY . /code
EXPOSE 8000
CMD ["gunicorn", "--bind", "0.0.0.0:8000", "--log-file", "-", "podrings.wsgi"]
