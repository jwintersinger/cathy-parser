Cathy Parser
============

A querier for file index records.
---------------------------------

Cathy Parser queries the records produced by [Cathy](http://www.mtg.sk/rva/), a
file-indexing application helpful in cataloguing files stored on removeable
media. Back in my Windows-using days, I had indexed several hundred discs, but
found myself unable to use the resulting records from the Linux command-line
environment that I now prefer. As Cathy stores its records in an undocumented
binary blob, I reverse-engineered its file format and implemented a parser in
Python.
