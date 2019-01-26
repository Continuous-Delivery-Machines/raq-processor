FROM python:3.7

WORKDIR /app

COPY requirements.txt /app/requirements.txt
RUN pip install -r requirements.txt

COPY src /app

CMD ["python", "src/sql_manager.py"]