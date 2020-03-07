# Readme For Avito Scrapers
## webbot.py
webbot.py is a source code clone from [here](https://github.com/nateshmbhat/webbot). Thanks to this guy.
This was changed: `driverpath = ('chrome_windows.exe')` in Browser class initialization.
That means you need chrome_windows.exe in the same dir as webbot.py or to define another `driverpath` for your driver.
This was done to overcome some issues with pyinstaller.
