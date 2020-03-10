# Readme For Avito Scraper

Tested on Python 3.8.1 [MSC v.1916 32 bit (Intel)] on win32.

I suggest to use VPN (i use ProtonVPN) if your IP has been blocked, that would be much faster then proxies in proxies.txt.

## webbot py

webbot.py is a source code clone from [here](https://github.com/nateshmbhat/webbot). Thanks to this guy.
This was changed: `driverpath = ('chrome_windows.exe')` in Browser class initialization.
That means you need chrome_windows.exe in the same dir as webbot.py or to define another `driverpath` for your driver.
This was done to overcome some issues with pyinstaller.

## avito_scraper.py

This is the main file which should be launched.

## core py

Core scraper functions.

## utils py

Fuctions for reading, writing, formatting etc.

## settings py

Here you may want to specify `WEBDRIVERPATH` (in my case chrome_windows.exe) if you want to make executable. Or use just requests by changing `USE_BOT=False`. Also changing `SLEEP_TIME` and `TIMEOUT` may affect the performance.

## proxies txt

Using these should work but will likely make bot crawl like a snail.
Use `TIMEOUT` in settings.py to move faster to next proxy if it takes too long.
Also change `SLEEP_TIME` if server blocks ip's too fast.

## bad_proxies txt

All used proxies are cloned here.

## errors txt

A place for errors that reaches max tries.

## chrome_windows exe

You won't find it here, but you can find it on your system after installing selenium. However you can avoid using it by changing `USE_BOT=False` in setting.py. IMHO selenium is blocked less frequent by servers.