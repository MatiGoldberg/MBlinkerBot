#!/usr/bin/python

from BotClient import BotClient

def main():
	print "--TelegramBot Wrapper--"
	client = BotClient()
	client.Test()
	client.RunLoop()
	#client.RunOnce()

if __name__ == '__main__':
	main()