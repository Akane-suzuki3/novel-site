FROM python:3.12-slim

WORKDIR /app

# 依存パッケージをコピー＆インストール
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# アプリ本体をコピー
COPY . .

# FastAPI を uvicorn で起動
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
