![SubDB - a free subtitle database](http://thesubdb.com/subdb-logo.png)

#README

Pyrrot is a multiplatform client for [SubDB](http://thesubdb.com "SubDB - a free subtitle database") written in Python. It can run on Windows, Linux and MacOS.


##REQUIREMENTS

- Python 2.6.5 for all systems.
- Mark Hammond's Win32all if you want to run Pyrrot as a service on Windows.


##INSTALLING

You need to copy Pyrrot2.py and urllib2_file.py to a folder of your preference. Then, after you've done with the configurations (see below), all you need to do is:

`python Pyrrot2.py`
or
`c:\Python2.6.5\python.exe c:\path\to\Pyrrot2.py (if you're using windows)`

You can also run Pyrrot using cron, or install Pyrrot as a Windows service. To do this:

Cron (Linux):
`*/30	*	*	*	*	python /path/to/Pyrrot2.py`

Service (Windows):
`c:\Python2.6.5\python.exe c:\path\to\Pyrrot2Service.py --startup auto install`

As you may have noticed, you need to copy Pyrrot2Service.py too.


##CONFIGURATION

You need to edit the following lines on Pyrrot2.py before use it:

`PYRROT_DIR = "/path/to/pyrrot" #The path to where Pyrrot is. Can be empty if you're not running Pyrrot as a Windows Service.`

`DIRECTORIES = ["/path/to/your/video/files", "/path/to/your/video/files2"] #Configure here the directories where your video files are.`

`LANGUAGES = ["pt", "en"] #The languages to download subtitles, in order of preference.`

`MOVIE_EXTS = ['.avi', '.mkv', '.mp4', '.mov', '.mpg', '.wmv'] #The video file extensions that you want Pyrrot to looking for.`

`SUBS_EXTS = ['.srt', '.sub'] #The subtitle extensions that you want Pyrrot to looking for.`

If you are on Windows, the paths will be like:

`PYRROT_DIR = "c:\\path\\to\\pyrrot"`


##FOUND A BUG

<http://github.com/jrhames/pyrrot-cli/issues>


##LICENSE

This software is distribute under Creative Commons Attribution-Noncommercial-Share Alike 3.0. You can read the entire license on:
<http://creativecommons.org/licenses/by-nc-sa/3.0/>
