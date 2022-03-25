#!/usr/bin/env python3
import getopt
import sys

SEP = ","

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
column_position = {}

SAMPLE_ID_POS = 6

OUTPUT_COLUMNS = \
    ['Date', 'Time', 'ID', 'F', 'F0', 'Fm', 'Fm\'', 'Epar', 'Y(II)', 'ETR', 'Fv/Fm', 'NPQ', 'deltaNPQ', 'rETR']


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
        self.f_section_counter = 0
        self.npq_zero = -1
        self.delta_npq = 0.0
        self.sample_id = sample_id
        self.line_buffer = []

    def append(self, values):
        self.line_buffer.append(values)

    def write_to_file(self, file_handle):
        for line in self.line_buffer:
            write_list(file_handle, line)

    def get_first_date_time(self):
        return '{} {}'.format(self.line_buffer[0][0], self.line_buffer[0][1]) if len(self.line_buffer) > 0 else "N/A"


def calc_r_etr(par, yii):
    return '-' if yii == '-' else round(float(par) * float(yii), 2)


def get_value(raw_fields, column_name):
    if column_name in column_position:
        return raw_fields[column_position[column_name]].strip("\"\n")
    else:
        return 'NA'


def get_record_type(raw_fields):
    return get_value(raw_fields, COL_TYPE) if len(raw_fields) > 4 else 'N/A'


def write_list(f, values):
    string_list = [str(v) for v in values]
    f.write('{}\n'.format(SEP.join(string_list)))


def process_raw_lines(raw_lines, output_file):
    f_section_counter = 0
    for raw_line in raw_lines:
        raw_fields = raw_line.split(SEP)
        record_type = get_record_type(raw_fields)
        if record_type == 'SLCS':
            f_section_counter += 1
            sample_id = raw_fields[SAMPLE_ID_POS].strip("\"\n")
            light_curve = LightCurve(raw_fields[SAMPLE_ID_POS].strip("\"\n"))
        elif record_type == 'SLCE':
            if f_section_counter != 10:
                print('Warning: less than 10 records ({}) found in line curve ({})'.
                      format(f_section_counter, light_curve.get_first_date_time()))
            else:
                light_curve.write_to_file(output_file)
            f_section_counter = 0
        elif record_type == 'FO':
            f_section_counter += 1
            o = OutputRow(raw_fields)
            light_curve.f = o.f
            light_curve.append([o.date, o.time, light_curve.sample_id, o.f, o.f, o.fm, o.fm_prime, o.par, o.yii, o.etr,
                        o.fvfm_raw, o.npq, 0.0, o.r_etr])
        elif record_type == "F":
            f_section_counter += 1
            o = OutputRow(raw_fields)
            if light_curve.npq_zero == -1:
                light_curve.npq_zero = -1 if o.npq == '-' else float(o.npq.replace(' ', ''))
            if f_section_counter == 9:
                light_curve.delta_npq = '-' if o.npq == '-' else round(float(o.npq.replace(' ', '')) - light_curve.npq_zero, 3)
            light_curve.append([o.date, o.time, light_curve.sample_id, o.f, light_curve.f, o.fm, o.fm_prime, o.par, o.yii, o.etr,
                        o.fvfm_raw, o.npq, light_curve.delta_npq, o.r_etr])


def open_files(data_path, output_path):
    with open(data_path) as raw_file:
        raw_lines = raw_file.readlines()

    # read the column names from the raw file to figure out their positions
    for line in raw_lines:
        if 'Datetime' in line:
            line_with_headers = line.split(SEP)
            for idx, col in enumerate(line_with_headers):
                column_position[col.strip("\"\n")] = idx
            break
    if COL_DATETIME not in column_position.keys():
        exit("At least one line in the raw PAM data file must contain the headers like Datetime, etc.")

    with open(output_path, "w") as output_file:
        write_list(output_file, OUTPUT_COLUMNS)
        process_raw_lines(raw_lines, output_file)


def main(argv):
    data_path = ''
    output_path = ''
    opts, args = getopt.getopt(argv, "d:i:o:", ["data=", "ids=", "output="])
    for opt, arg in opts:
        if opt in ("-d", "--data"):
            data_path = arg
        elif opt in ("-o", "--output"):
            output_path = arg
    open_files(data_path, output_path)


if __name__ == "__main__":
    main(sys.argv[1:])
