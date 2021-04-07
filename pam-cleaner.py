#!/usr/bin/env python3
import sys, getopt

SEP = ";"

COL_DATETIME = "Datetime"
COL_DATE = "Date"
COL_TIME = "Time"
COL_TYPE = "Type"
COL_NO = "No."
COL_1F = "1:F"
COL_1FM = "1:Fm'"
COL_1PAR = "1:PAR"
COL_1Y = "1:Y (II)"
COL_1ETR = "1:ETR"
COL_1FO = "1:Fo'"
COL_1NPQ = "1:NPQ"
COL_FVFM = "1:Fv/Fm"
column_position = {}


class OutputRow:
    ETR_FACTOR = 0.84
    PSII_FACTOR = 0.5
    # yii = (fm - f0) / fm
    # etr = par * ETR_FACTOR * PSII_FACTOR * yii

    def __init__(self, raw_fields):
        self.time = get_value(raw_fields, COL_TIME)
        self.f = get_value(raw_fields, COL_1F)
        self.fm_prime = get_value(raw_fields, COL_1FM)
        self.par = get_value(raw_fields, COL_1PAR)
        self.yii = get_value(raw_fields, COL_1Y)
        self.etr = get_value(raw_fields, COL_1ETR)
        self.npq = get_value(raw_fields, COL_1NPQ)
        self.f0 = get_value(raw_fields, COL_1FO)
        self.fm = get_value(raw_fields, COL_1FM)
        self.fvfm_raw = get_value(raw_fields, COL_FVFM)
        self.rETR = calc_rETR(self.par, self.yii)


def calc_rETR(par, yii):
    return '-' if yii == '-' else round(float(par) * float(yii), 2)


def get_value(raw_fields, column_name):
    if column_name in column_position:
        return raw_fields[column_position[column_name]].strip("\"\n")
    else:
        return None


def process_id_line(id_fields, raw_lines, output_file):
    date = id_fields[0].strip("\"")
    time_id = id_fields[1].strip("\"")
    id = id_fields[2].strip("\"")
    fvfm_id = id_fields[3].strip("\"")
    notes = id_fields[4].strip("\n")
    f_section_counter = 0
    npq_zero = -1
    deltaNPQ = 0.0
    for raw_line in raw_lines:
        raw_fields = raw_line.split(";")
        if len(raw_fields) > 4:
            record_type = get_value(raw_fields, COL_TYPE)
        else:
            record_type = "N/A"
        if record_type == "SLCE" and f_section_counter > 0:
            if f_section_counter != 9:
                output_file.write("Error: less than 9 F records found in section ({})".format(f_section_counter))
            break
        elif date in raw_line and time_id in raw_line and record_type == "FO":
            f_section_counter += 1
            o = OutputRow(raw_fields)
            output_file.write("{};{};{};{};{};{};{};{};{};{};{};{};{};{};{}\n".format(
                date, o.time, id, o.f, o.f0, o.fm, o.fm_prime, o.par, o.yii, o.etr, o.fvfm_raw, o.npq, 0.0, o.rETR, notes))
        elif record_type == "F" and f_section_counter > 0:
            f_section_counter += 1
            o = OutputRow(raw_fields)
            if npq_zero == -1:
                npq_zero = -1 if o.npq == '-' else float(o.npq.replace(' ', ''))
            if f_section_counter == 9:
                deltaNPQ = '-' if o.npq == '-' else round(float(o.npq.replace(' ', '')) - npq_zero, 3)
            output_file.write("{};{};{};{};{};{};{};{};{};{};{};{};{};{};{}\n".format(
                date, o.time, id, o.f, o.f0, o.fm, o.fm_prime, o.par, o.yii, o.etr, o.fvfm_raw, o.npq, deltaNPQ, o.rETR, notes))


def open_files(data_path, ids_path, output_path):
    with open(data_path) as raw_file:
        raw_lines = raw_file.readlines()

    # read the column names from the raw file to figure out their positions
    first_line = raw_lines[0].split(SEP)
    for idx, col in enumerate(first_line):
        column_position[col.strip("\"\n")] = idx
    if COL_DATETIME not in column_position.keys():
        exit("The first line in the raw PAM data file must contain the headers like Datetime, etc.")

    with open(ids_path) as id_file:
        id_lines = id_file.readlines()
    if '"Date"' not in id_lines[0]:
        exit('The first line in the sample ID file must contain the headers like "Date";"Time";"ID";"Fv/Fm";"Notes"')

    with open(output_path, "w") as output_file:
        output_file.write("Date;Time;ID;F;F0;Fm;Fm\';Epar;Y(II);ETR;Fv/Fm;NPQ;deltaNPQ;rETR;Notes\n")
        for id_line in id_lines:
            id_file_columns = id_line.split(SEP)
            if id_file_columns[0] != "\"Date\"":
                process_id_line(id_file_columns, raw_lines, output_file)


def main(argv):
    data_path = ''
    ids_path = ''
    output_path = ''
    opts, args = getopt.getopt(argv, "d:i:o:", ["data=", "ids=", "output="])
    for opt, arg in opts:
        if opt in ("-d", "--data"):
            data_path = arg
        elif opt in ("-i", "--ids"):
            ids_path = arg
        elif opt in ("-o", "--output"):
            output_path = arg
    open_files(data_path, ids_path, output_path)


if __name__ == "__main__":
    main(sys.argv[1:])
