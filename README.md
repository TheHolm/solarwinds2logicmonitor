# solarwinds2logicmonitor
Simple tool to move nodes from Solarwinds to LogicMonitor

# Archived 
(19/07/2022) Sorry folks, but this project is archived now.  I have no plan to develop it more. 

## File tree structure
TBA

## solarwinds2file.py
Quick and dirty code to import all nodes from solarwinds to tree like file structure. Should be used only once during initial import.
Controlled by "[solarwinds]" section of config.ini

## file2logicmonitor
Create/update nodes in LogicMonitor based on file tree.

# FAQ

Q. Why custom code for LM? There is Uses [logicmonitor_sdk](https://pypi.org/project/logicmonitor-sdk/) package to access LM.
A. I wish that package works. But unfortunately it is not.
