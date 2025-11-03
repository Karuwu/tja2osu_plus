# tja2osu_plus
a modified version of tja2osu which fixes incorrect conversion for charts with measure changes.
added features:
- course and level filter
- option to export as osz
- can pick which branches to convert

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

Additionally, you can choose to keep folder structure the same as the input directory in the output folder. Not available if a single tja file is selected.

<img width="634" height="459" alt="Screenshot 2025-11-03 at 04 22 10" src="https://github.com/user-attachments/assets/a63fb019-1723-40d6-874b-34e9532d402b" />



### 3. Beatmap Data (optional) </ins>
You can also specify the Artist and Creator name if you want. Leaving these spaces empty will default the Artist name to _Various_, and Creator name to _tja2osu_

<img width="641" height="72" alt="Screenshot 2025-11-03 at 04 20 12" src="https://github.com/user-attachments/assets/9a96584d-4974-457f-9098-91a5fabe3c98" />


### 4. Filters (optional)
Here you can select a number of filters for conversion. 

#### <ins>Course and Level</ins>
Select which courses/levels you want to be converted. 

These filters are additive, so for example if you pick both Oni and 6 star filters, then only 6 star Oni charts will be converted.

<img width="470" height="59" alt="Screenshot 2025-11-03 at 04 29 41" src="https://github.com/user-attachments/assets/ab30ce2d-8fef-4517-9349-2eb1a1557694" />

#### <ins>Skip Double</ins>
Option to skip all conversion of Double charts (双打) 

#### <ins>Export as .osz</ins>
Option to export the outputted files into a .osz file. Useful for if you want to open directly in osu.

Bonus options to copy audio into .osz, or keep the output of osu files in the output folder.

(This option is disabled if you selected a single tja file to convert)
<img width="589" height="63" alt="Screenshot 2025-11-03 at 04 31 04" src="https://github.com/user-attachments/assets/9e1fca01-548e-4220-80d3-2e077155b70e" />

#### <ins>Branch</ins>
Select which branch you want to be converted. If selected multiple branches, then each branch will be exported as an individual osu file. Only applicable for branched charts (if not branched, this option is ignored)

<img width="438" height="37" alt="Screenshot 2025-11-03 at 04 26 32" src="https://github.com/user-attachments/assets/c32b26c8-7c38-4590-bf8f-a07386c4802d" />

### 5. Convert
After picking all your options, simply click Convert and your osu file will be in the output folder!
