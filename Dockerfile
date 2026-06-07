FROM python:3.12-slim

WORKDIR /app

RUN pip install --no-cache-dir uv

COPY backend/requirements.txt .
RUN uv pip install --system --no-cache -r requirements.txt

COPY backend/ .

RUN mkdir -p uploads data

EXPOSE 8000

CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8000"]
