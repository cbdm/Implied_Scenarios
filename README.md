# Implied_Scenarios

Relevant files used for the project _'Characterization of Implied Scenarios as Families of Common Behavior'_.

## How do I get set up?

[Code](code/) and [Data](data/) are in their respective folders, while the modified LTSA-MSC plugin is in this root folder. **Each folder contains a readme that better explains their files usage**. An overview of the contents is presented below:

###### Python code
Everything was developed and tested on version 3.6.3, and libraries used are in the [requirements file (inside code folder).](code/requirements.txt) Note that you need [_Graphviz_](https://www.graphviz.org) installed to be able to use anytree's export method.

###### LTSA
The provided plugin (mscplugin_mod.jar) is a modified version of [the original LTSA-MSC by Uchitel et al.](https://www.doc.ic.ac.uk/ltsa/msc/)
It is able to collect multiple implied scenarios iteratively and export them to a text file.
To use it, simply replace the original one in LTSA's plugins folder.


## Who do I talk to?

caio.batista@gmail.com
