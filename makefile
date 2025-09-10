all: run


run:
	@mitmproxy -s main.py 

test:
	@mitmdump -s main.py
	@pyyest

