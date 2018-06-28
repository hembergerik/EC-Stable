FROM alpine:3.6

COPY . /app
WORKDIR /app

RUN apk add --no-cache python3

CMD [ "python3", "./pony_ea.py" ]