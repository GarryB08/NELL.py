FROM python:3.11-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .

EXPOSE 8501
CMD ["streamlit", "run", "NELL.py.py", "--server.address=0.0.0.0", "--server.port=8501", "--server.headless=true"]
