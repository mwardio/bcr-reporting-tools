FROM python:3.12-slim

EXPOSE 8503

WORKDIR /app

# dont write pyc files
# dont buffer to stdout/stderr
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

COPY ./ ./

RUN pip install -r requirements.txt

CMD ["streamlit", "run", "app.py", "--server.port=8502", "--server.address=0.0.0.0"]