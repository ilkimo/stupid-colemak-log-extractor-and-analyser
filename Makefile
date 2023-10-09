

build:
	docker build -t telegram-analysis .

run:
	docker run -d -v .:/app telegram-analysis

clean:
	rm *.html
	sudo rm -rf build
