# CODE (Implied_Scenarios)

In this folder the code used for our results is presented. **_requirements.txt_** list the required libraries for these scripts to run. Sample files can be found inside the [examples folder](examples/) to run these scripts. More examples can also be found inside the [data folder](../data/).

All scripts have comments that (I believe) explain ~~well~~ what they're doing. However, all 3 files are detailed below:

## analyze.py
  This is the main script used to analyze a list of implied scenarios. It takes as input the _txt_ file exported by our modified version of the LTSA-MSC plugin and exports the detected Common Behaviors (CBs), the results of the SW algorithm applied to the pairs of CBs detected, the Levenshtein distance between the pairs of CBs detected, two dendrograms showing the most similar CBs, and a test file to be used with the _check\_scenarios.py_ script (detailed below).

  The usage of this script is as follows:

```
python analyze.py traces_file
```

  where traces_file is a file containing the collected ISs by LTSA-MSC (such as [example_traces](examples/example_traces.txt)).

  Finally, all exported files are explained below:

###### CBs\_for\_[input file\].txt
  This file contains the detected Common Behaviors (CBs) among the collected ISs. This file is simply a list with one CB per line.

###### dendro\_for\_lev\_[input file\].pdf
  This is a pdf with 4 pages. Each page shows the [agglomerative hierarchical clustering](https://en.wikipedia.org/wiki/Hierarchical_clustering) with a different linkage method. Through a qualitative analysis, we realized that [Ward's method](https://en.wikipedia.org/wiki/Ward%27s_method) provided the best results overall, even though they were not that different.

  This dendrogram was obtained by hierarchical clustering the CBs with the Levenshtein distance.

###### dendro\_for\_sw\_[input file\].pdf
  This file is similar to the above one, however, the dissimilarity between two CBs for this dendrogram is calculated as follows:

```
                   ┌ 0,                   if cb1 = cb2
diss (cb1, cb2) =  ├ 1,                   if SW(cb1, cb2) = 0
                   └ 1 / SW(cb1, cb2),    otherwise.
``` 

  where _cb1_ and _cb2_ are CBs, and _SW(cb1, cb2)_ is the SW score for that pair of CBs.

###### lev\_for\_[input file\].csv
  This file contains the Levenshtein distance for each pair of CBs. It is a matrix and an element _A[i,j]_ is the distance between CB[i] and CB[j].

###### lev\_for\_[input file\].txt
  This file also presents the Levenshtein distances. It shows the distance and the messages of each CB for all pairs of CBs, and it's sorted in descending order, that is, the pairs with lowest distance will show up first. 

###### sw\_for\_[input file\].csv
  This file contains the Smith-Waterman (SW) score for each pair of CBs. It is a matrix and an element _A[i,j]_ is the SW score between CB[i] and CB[j].

###### sw\_for\_[input file\].txt
  This file also presents the SW results. However, it's not simply the traceback scores. It shows the score and alignment for all pairs of CBs, and it's sorted in descending order, that is, the pairs with higher score (i.e., most similar) will show up first. 

###### tests\_for\_[input file\].txt
  Finally, this file can be used to test the presence of ISs in the model. This is achieved by using the check_scenarios.py script and the Architecture or Constrained model.

## check_traces.py
  This file can be used to check if traces are reachable in a FSP specification. That is, it is possible to check if ISs are present in the architecture model generated by LTSA.

  The usage of this script is as follows:

```
python check_scenarios.py fsp_spec [test_file] [-DRAW]
```

  where _fsp\_spec_ is the system's composition from LTSA (such as [example_fsp](examples/example_fsp.lts)), _tests\_file_ is a file containing the ISs that should be tested (such as [example_tests](examples/example_tests.txt)), and the _-DRAW_ is an optional flag to draw the automata for the given specification.

  As LTSA doesn't draw automatas that are too large, this is an alternative to visualize the model's specification.

  Note that this can be used with 2 or 3 parameters, but the first one always has to be the FSP specification. It can be used to only test for reachable traces, only draw the specification's automata, or both checking and drawing. For the latter (3 parameters), it is important to keep the order stated above: fsp_spec test_file -DRAW.

  Examples for FSP specifications and tests files can be found in the [data folder](../data/). Each model subfolder has its own Architecture and Constrained models in FSP format, and inside their results folder there is the test file to be used with those models.

## model_parser.py
  This script is used to generate a XML file that works with LTSA-MSC tool containing the scenarios of a model's specification. Its input is a file that has a much simpler syntax, and can generate both the XML file and a the positive scenarios to be used with the script above (_check\_scenarios_). These positives scenarios ~~should~~ can be included in the output test file from the _analyze.py_ script.

  [**_example\_model.txt_**](examples/example_model.txt) is a sample file that explains well how the syntax for the input file works. Inside the [data folder](../data/) more examples of this kind of file can be found.

  The usage of this script is as follows:

```
python model_parser.py input_file [-t]
```

  where _input\_file_ is the _txt_ file using the syntax stated above, and _-t_ is an optional flag used to export the positive scenarios of the model's specification.