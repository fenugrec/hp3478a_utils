## ###
#  IP: GHIDRA
# 
#  Licensed under the Apache License, Version 2.0 (the "License");
#  you may not use this file except in compliance with the License.
#  You may obtain a copy of the License at
#  
#       http://www.apache.org/licenses/LICENSE-2.0
#  
#  Unless required by applicable law or agreed to in writing, software
#  distributed under the License is distributed on an "AS IS" BASIS,
#  WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#  See the License for the specific language governing permissions and
#  limitations under the License.
##
#
# modified from builtin ghidra script "ImportSymbolsScript.py"
#
# Import labels from a d48 "ctl" file, with this format :
#
# "l <addr> <label_text>"
# "! <addr> <EOL comment>"
# "# <addr> <plate (inline) comment>"

# Address formats are the same as those that can be used with the "Go to address" function. For example:
# - 1234abcd
# - 0x1234abcd
# - ADDRESS_SPACE:1234abcd
# - ADDRESS_SPACE:0x1234abcd
# - MEMORY_REGION:1234abcd
# - MEMORY_REGION:0x1234abcd
#
# @author fenugrec 2022
# @category Symbol
#

from ghidra.program.model.symbol.SourceType import *
import string

functionManager = currentProgram.getFunctionManager()

fname = askFile("select d48 ctl file", "OK")

#with open(fname.absolutePath) as f:
for line in file(fname.absolutePath):  # note, cannot use open(), since that is in GhidraScript
	cleanline = line.rstrip()
	pieces = cleanline.split(None,2)	#maxsplit = 2 because last element (comment text) could contain whitespace

	try:
		text = pieces[2]
	except IndexError:
		continue

	type = pieces[0]
	address = toAddr(pieces[1])

	if type[0] not in "l!#":
		#skip lines not starting with recognized types
		continue

	if address is None:
		print("problem with line {}".format(pieces))
		continue

	if type == "l":
		clean_label = text.split()[0]
		print("Created label {} @ {}".format(clean_label, address))
		createLabel(address, clean_label, False)
	elif type == "!":
		print("comment @ {}: {}".format(address, text))
		setEOLComment(address, text)
	elif type == "#":
		print("plate comment @ {}: {}".format(address, text))
		setPreComment(address, text)
