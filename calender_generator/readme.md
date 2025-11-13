Excel Calendar GeneratorThis script reads a config.json file to generate a 12-month calendar in an Excel (.xlsx) file, with specific dates color-coded based on defined occasions.


How to RunInstall Dependencies:You must have the openpyxl library installed.

pip install openpyxl



Edit the Configuration:Open the config.json file and modify it to your needs.calendar_year: The year you want to generate.Add or remove "occasion" blocks (like "pi_planning", "release_windows", etc.).Each occasion must have a dates list (using "dd/mm/yyyy" format) and a colour_code.Valid colour_code options are: "blue", "green", "red", "yellow", "purple".Run the Script:Once your config.json is ready, run the Python script from your terminal:python create_calendar.py
Check the Output:If successful, a new file named Mosaic_AI_Release_Calendar.xlsx will be created in the same directory.
