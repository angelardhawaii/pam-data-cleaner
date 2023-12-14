#!/usr/bin/env python3
import argparse
import glob
import os.path
import pathlib
import sys

OUTPUT_SEPARATOR = ","

COL_DATETIME = "Datetime"
COL_DATE = "Date"
COL_TIME = "Time"
COL_TYPE = "Type"
COL_NO = "No."
COL_1F = "1:F"
COL_1FM = "1:Fm"
COL_1FM_PRIME = "1:Fm'"
COL_1PAR = "1:PAR"
COL_1Y = "1:Y (II)"
COL_1ETR = "1:ETR"
COL_1FO = "1:Fo'"
COL_1NPQ = "1:NPQ"
COL_FVFM = "1:Fv/Fm"

SAMPLE_ID_POS = 6

OUTPUT_COLUMNS = \
    ['Date', 'Time', 'ID', 'F', 'F0', 'Fm', 'Fm\'', 'Epar', 'Y(II)', 'ETR', 'Fv/Fm', 'NPQ', 'deltaNPQ', 'rETR']


column_position = {}
input_separator = ''


class OutputRow:
    ETR_FACTOR = 0.84
    PSII_FACTOR = 0.5

    def __init__(self, raw_fields):
        self.date = get_value(raw_fields, COL_DATE)
        self.time = get_value(raw_fields, COL_TIME)
        self.f = get_value(raw_fields, COL_1F)
        self.fm_prime = get_value(raw_fields, COL_1FM_PRIME)
        self.par = get_value(raw_fields, COL_1PAR)
        self.yii = get_value(raw_fields, COL_1Y)
        self.etr = get_value(raw_fields, COL_1ETR)
        self.npq = get_value(raw_fields, COL_1NPQ)
        self.f0 = get_value(raw_fields, COL_1FO)
        self.fm = get_value(raw_fields, COL_1FM)
        self.fvfm_raw = get_value(raw_fields, COL_FVFM)
        if self.yii == "-" and float(self.fm_prime) != 0:
            self.yii = round((float(self.fm_prime) - float(self.f)) / float(self.fm_prime), 3)
        if self.yii != "-" and self.etr == "-":
            self.etr = round(float(self.par) * self.ETR_FACTOR * self.PSII_FACTOR * float(self.yii), 2)
        self.r_etr = calc_r_etr(self.par, self.yii)


class LightCurve:
    def __init__(self, sample_id):
        self.npq_zero = -1
        self.delta_npq = 0.0
        self.sample_id = sample_id
        self.line_buffer = []

    def append(self, values):
        self.line_buffer.append(values)

    def get_number_of_records(self):
        return len(self.line_buffer)

    def write_to_file(self, file_handle):
        for line in self.line_buffer:
            write_list(file_handle, line)

    def get_first_date_time(self):
        return '{} {}'.format(self.line_buffer[0][0], self.line_buffer[0][1]) if len(self.line_buffer) > 0 else "N/A"


def calc_r_etr(par, yii):
    return '-' if yii == '-' else round(float(par) * float(yii), 2)


def get_value(raw_fields, column_name):
    if column_name in column_position:
        p = column_position[column_name]
        if p >= len(raw_fields):
            print(f'Cannot find data for column {column_name} in row {raw_fields}', file=sys.stderr)
            exit(1)
        return raw_fields[column_position[column_name]].strip("\"\n")
    else:
        return 'NA'


def get_record_type(raw_fields):
    return get_value(raw_fields, COL_TYPE) if len(raw_fields) > 4 else 'N/A'


def write_list(f, values):
    string_list = [str(v) for v in values]
    f.write('{}\n'.format(OUTPUT_SEPARATOR.join(string_list)))


def process_raw_lines(raw_lines, output_file):
    light_curve = {}
    for raw_line in raw_lines:
        raw_fields = raw_line.split(input_separator)
        record_type = get_record_type(raw_fields)
        if record_type == 'SLCS':
            light_curve = LightCurve(raw_fields[SAMPLE_ID_POS].strip("\"\n"))
        elif record_type == 'SLCE':
            if light_curve.get_number_of_records() != 9:
                n = light_curve.get_number_of_records()
                l = raw_line.strip("\n")
                print(f'Warning: less than 9 records ({n}) found in line curve {l}')
            else:
                light_curve.write_to_file(output_file)
        elif record_type == 'FO':
            o = OutputRow(raw_fields)
            light_curve.f = o.f
            light_curve.append([o.date, o.time, light_curve.sample_id, o.f, o.f, o.fm, o.fm_prime, o.par,
                                o.yii, o.etr, o.fvfm_raw, o.npq, 0.0, o.r_etr])
        elif record_type == "F":
            o = OutputRow(raw_fields)
            if light_curve.npq_zero == -1:
                light_curve.npq_zero = -1 if o.npq == '-' else float(o.npq.replace(' ', ''))
            if light_curve.get_number_of_records() == 10:
                light_curve.delta_npq = '-' if o.npq == '-' \
                    else round(float(o.npq.replace(' ', '')) - light_curve.npq_zero, 3)
            light_curve.append([o.date, o.time, light_curve.sample_id, o.f, light_curve.f, o.fm, o.fm_prime, o.par,
                                o.yii, o.etr, o.fvfm_raw, o.npq, light_curve.delta_npq, o.r_etr])


def determine_column_positions(raw_lines):
    global input_separator
    # read the column names from the raw file to figure out their positions
    for line in raw_lines:
        input_separator = ';' if ';' in line else ','
        if 'Datetime' in line:
            line_with_headers = line.split(input_separator)
            for idx, col in enumerate(line_with_headers):
                column_position[col.strip("\"\n")] = idx
            break
    if COL_DATETIME not in column_position.keys():
        exit("At least one line in the raw PAM data file must contain the headers like Datetime, etc.")


def open_files(data_path, output_path):
    global column_position
    output_dir = os.path.dirname(output_path)
    pathlib.Path(output_dir).mkdir(parents=True, exist_ok=True)
    filenames = glob.glob(data_path)
    with open(output_path, "w") as output_file:
        write_list(output_file, OUTPUT_COLUMNS)
        for filename in filenames:
            with open(filename) as raw_file:
                raw_lines = raw_file.readlines()
            determine_column_positions(raw_lines)
            process_raw_lines(raw_lines, output_file)


def main(argv):
    parser = argparse.ArgumentParser(description='Cleans raw PAM data from multiple WinControl files and creates a '
                                                 'single file in a convenient format for analysis with R')
    parser.add_argument('-d', '--data',required=True, help='Path to the WinControl files. It accepts wildcards like ''*.csv''.')
    parser.add_argument('-o', '--output', required=True, help='Output file name where the results are saved.')
    args = parser.parse_args()
    data_path = args.data
    output_path = args.output
    open_files(data_path, output_path)


if __name__ == "__main__":
    main(sys.argv[1:])
