#!/usr/bin/python

from BotClient import BotClient

def main():
	print "--TelegramBot Wrapper--"
	client = BotClient()
	client.run_loop()
	#client.run_once()

if __name__ == '__main__':
	main()