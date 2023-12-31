FROM python:3.9-slim

WORKDIR /app

RUN pip install matplotlib beautifulsoup4 imageio[ffmpeg] pandas

COPY . /app

CMD ["python", "./colemak_telegram_analysis.py"]
