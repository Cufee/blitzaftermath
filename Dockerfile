FROM python:3.8-slim

# Set the working directory.
WORKDIR /app

# Copy the file from your host to your current location.
COPY . .

RUN pip3 install -r requirements.txt

ENTRYPOINT [ "python3" ]

CMD [ "bot.py" ]