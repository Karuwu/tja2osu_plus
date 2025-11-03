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

<img width="634" height="459" alt="Screenshot 2025-11-03 at 04 22 10" src="https://github.com/user-attachments/assets/a63fb019-1723-40d6-874b-34e9532d402b" />



### 3. Beatmap Data (optional) </ins>
You can also specify the Artist and Creator name if you want. Leaving these spaces empty will default the Artist name to _Various_, and Creator name to _tja2osu_

<img width="641" height="72" alt="Screenshot 2025-11-03 at 04 20 12" src="https://github.com/user-attachments/assets/9a96584d-4974-457f-9098-91a5fabe3c98" />


### 4. Filters (optional)
Here you can select a number of filters for conversion. 

#### <ins>Course</ins>
- Select which courses you want to be converted. (Default - only convert Oni/Inner Oni courses)
<img width="451" height="30" alt="Screenshot 2025-11-03 at 04 25 09" src="https://github.com/user-attachments/assets/bc96aa2e-140c-4505-b25b-76497cb00b9d" />

#### <ins>Level</ins>
- Select which levels (stars) you want to be converted. Useful for large directories containing many tja files.
<img width="466" height="34" alt="Screenshot 2025-11-03 at 04 25 46" src="https://github.com/user-attachments/assets/32303f6c-d9eb-4fa5-b6b6-feb1d3b462b0" />

Note: these filters are additive, so if you pick both Oni and 6 star filters, then only 6 star Oni charts will be converted.

#### <ins>Skip Double</ins>
- Option to skip all conversion of Double charts (双打) 

#### <ins>Export as .osz</ins>
- Option to export the outputted files into a .osz file. Useful for if you want to open directly in osu.
- Bonus options to copy audio into .osz, or keep the output of osu files in the output folder.
<img width="580" height="60" alt="Screenshot 2025-11-03 at 04 26 07" src="https://github.com/user-attachments/assets/f14b4c63-1713-4757-95fb-58d8739f6aff" />

#### <ins>Branch</ins>
- Select which branch you want to be converted. If selected multiple branches, then each branch will be exported as an individual osu file. Only applicable for branched charts (if not branched, this option is ignored)

<img width="438" height="37" alt="Screenshot 2025-11-03 at 04 26 32" src="https://github.com/user-attachments/assets/c32b26c8-7c38-4590-bf8f-a07386c4802d" />

### 5. Convert
After picking all your options, simply click Convert and your osu file will be in the output folder!
