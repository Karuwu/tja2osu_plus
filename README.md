# tja2osu_plus
a modified version of tja2osu which fixes incorrect conversion for charts with measure changes.
added features:
-
also added more options and filters for main.py, and the ability to export the converted chart as .osz directly.


## Usage
### 1. Open main.py

```sh
python main.py
```
You should then see a window pop up, looking like this:

<img width="662" height="585" alt="Screenshot 2025-11-03 at 04 00 32" src="https://github.com/user-attachments/assets/f147116b-5cec-4445-877a-26f4ae8175fa" />

### 2. Select paths
You need to specify an input path for the tja file. To do this, you can either type in the path manually or use the Browse options.
If you select **Browse File**, then simply select the tja file you wish to convert.
If you select **Browse Folder**, then select the folder containing the TJA file(s). 
Finally, select an output path. I recommend outputting to a new folder to contain all your converted maps.

<img width="823" height="641" alt="Screenshot 2025-11-03 at 03 42 50" src="https://github.com/user-attachments/assets/a11cf2af-b8a0-482b-be1b-7f5f137dd86f" />

### 3. Beatmap Data (optional)
You can also specify the Artist and Creator name if you want. Leaving these spaces empty will default the Artist name to _Various_, and Creator name to _tja2osu_

### 4. Filters (optional)
Here you can select a number of filters for conversion. 

#### Course
Select which courses you want to be converted. (Default - only convert Oni/Inner Oni courses)
#### Level
Select which levels (stars) you want to be converted. Useful for large directories containing many tja files.

Note: these filters are additive, so if you pick both Oni and 6 star filters, then only 6 star Oni charts will be converted.

#### Skip Double
Option to skip all conversion of Double charts (双打) 

#### Export as .osz
Option to export the outputted files into a .osz file. Useful for if you want to open directly in osu.
Bonus options to copy audio into .osz, or keep the output of osu files in the output folder.

#### Branch
Select which branch you want to be converted. If selected multiple branches, then each branch will be exported as an individual osu file. Only applicable for branched charts (if not branched, this option is ignored)

### 5. Convert
After picking all your options, simply click Convert and your osu file will be in the output folder!
