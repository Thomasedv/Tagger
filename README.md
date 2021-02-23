# Tagger
A very simple music renamer and tagger.

### WIP! Project is ~~newly uploaded!~~ barely alive ###

Simple renamer and song tagger to make your various downloaded songs be uniform in your music collection. 

This is a working version and all that, at least it should be. 

Current features:
* Load and bulk rename files where some things are formatted automatically with a filter. 
* Tag files with title and artist from the filename (And only that,for now at least)
* Bulk actions like remove parentheses, brackets and numbers, etc. 
* Highlights song names that don't have a ` - ` in between the title and artist, because those are needed to auto generate the tags from the filename. 
* Files are added with file creation date first, so most recent files will be at the top. 
* Tagging and writing filenames only happens when you press the `rename songs` button at the bottom. 
* The tag all button just generates title and artist name from the filenames, but isn't needed for writing the tags to the files.  
* A convenient log file written to with any potential errors, and all debug info. Will at least help me find problems if you have some.

Keep in mind, if your songs are in a protected folder by any antivirus programs, the rename will likely fail.   

Yet to be implemented features: 

* Change filtered words. Currently just custom words that i often encountered on some youtube videos. 
* The about menu at the top is empty and doesn't do anything atm, will link to this github eventually.
* Ability to generate file name from tag.

Please make an issue if you are interested in adding a feature or have a problem. I still use this myself, but haven't had the need for any additional features myself. 

Implementable on demand:
* Sort/load files based one something else than file creation date.
