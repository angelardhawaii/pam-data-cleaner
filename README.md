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
 

