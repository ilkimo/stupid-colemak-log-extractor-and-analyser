# stupid-colemak-log-extractor-and-analyser
This repository is useless for other people.

To use it, export Telegram chat in files. The generated files should be like:
messages.html
messages2.html
...

# Matching Regex
{layout=colemak_DH,wpm=(\d+(?:\.\d)?),accuracy=(\d+(?:\.\d)?%)\}

# Build Docker Image
```/bin/bash
docker build -t telegram-analysis .
```

# Run Docker Image
```/bin/bash
docker run -d -v $(pwd):/app telegram-analysis
```