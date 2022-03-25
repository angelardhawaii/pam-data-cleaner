
## pam-data-cleaner-2.0
Cleans raw PAM data from multiple WinControl files and creates a single file in a convenient format for analysis with R

Example:
`python3 pam-data-cleaner-2.0 -d example/pam_raw_with_id/*.csv -o output/clean.csv`

Reads all the `csv` files in the folder `example/pam_raw_with_id` and writes out the output to `output/clean.csv`.


# pam-data-cleaner
Takes raw data from PAM WinControl and turns it into a convenient format for analysis with R

## Usage

Example: 

`python3 pam-cleaner.py \
--data example/raw_pam_data.csv \
--ids example/sample_ids.csv \
--output example/cleaned-data.csv`

where 

* `ids` is the path to a file with date time and IDs of the fragments/specimens being measured
* `data` is the path to a file that contains an aggregate of all raw PAM files concatenated and sorted by date/time
* `output` is the where the output gets saved
 

