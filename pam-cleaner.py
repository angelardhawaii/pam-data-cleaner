#!/usr/bin/env python3
import sys, getopt

PAM_DATETIME = 0
PAM_DATE = 1
PAM_TIME = 2
PAM_TYPE = 3
PAM_F = 5
PAM_FM_PRIME = 6
PAM_PAR = 7
PAM_YIELD = 8
PAM_ETR = 9
PAM_NPQ = 10
PAM_FZERO = 11.
PAM_FM = 12
PAM_FV_FM = 13


def calc_rETR(par, yii):
    return '-' if yii == '-' else round(float(par) * float(yii), 2)


# check columns to make sure they match what is below. If not, change below
def process_id_line(id_fields, raw_lines):
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
            record_type = raw_fields[PAM_TYPE].strip("\"")
        else:
            record_type = "N/A"
        if record_type == "SLCE" and f_section_counter > 0:
            if f_section_counter != 9:
                print("Error: less than 9 F records found in section ({})".format(f_section_counter))
            break
        elif date in raw_line and time_id in raw_line and record_type == "FO":
            f_section_counter += 1
            time = raw_fields[PAM_TIME].strip("\"")
            f = raw_fields[PAM_F].strip("\"")
            fm_prime = raw_fields[PAM_FM_PRIME].strip("\"")
            par = raw_fields[PAM_PAR].strip("\"")
            yii = raw_fields[PAM_YIELD].strip("\"")
            etr = raw_fields[PAM_ETR].strip("\"")
            npq = raw_fields[PAM_NPQ].strip("\"")
            f0 = raw_fields[PAM_FZERO].strip("\"")
            fm = raw_fields[PAM_FM].strip("\"")
            fvfm_raw = raw_fields[PAM_FV_FM].strip("\"\n")
            rETR = calc_rETR(par, yii)
            # if fvfm_raw == '-' or fvfm_id == '-' or float(fvfm_id) != float(fvfm_raw):
            #     print("{};{};Error: Fv/Fm from ID file ({}) doesn't match Fv/Fm from raw file ({}).".format(date, time, fvfm_id, fvfm_raw))
            #     return
            print("{};{};{};{};{};{};{};{};{};{};{};{};{};{};{}".format(
                date, time, id, f, f0, fm, fm_prime, par, yii, etr, fvfm_raw, npq, 0.0, rETR, notes))
        elif record_type == "F" and f_section_counter > 0:
            f_section_counter += 1
            time = raw_fields[PAM_TIME].strip("\"")
            f = raw_fields[PAM_F].strip("\"")
            fm_prime = raw_fields[PAM_FM_PRIME].strip("\"")
            par = raw_fields[PAM_PAR].strip("\"")
            yii = raw_fields[PAM_YIELD].strip("\"")
            etr = raw_fields[PAM_ETR].strip("\"")
            npq = raw_fields[PAM_NPQ].strip("\"")
            f0 = raw_fields[PAM_FZERO].strip("\"")
            fm = raw_fields[PAM_FM].strip("\"")
            fvfm_raw = raw_fields[PAM_FV_FM].strip("\"\n")
            rETR = calc_rETR(par, yii)
            if npq_zero == -1:
                npq_zero = -1 if npq == '-' else float(npq.replace(' ', ''))
            if f_section_counter == 9:
                deltaNPQ = '-' if npq == '-' else round(float(npq.replace(' ', '')) - npq_zero, 3)
            print("{};{};{};{};{};{};{};{};{};{};{};{};{};{};{}".format(
                date, time, id, f, f0, fm, fm_prime, par, yii, etr, fvfm_raw, npq, deltaNPQ, rETR, notes))


# print('Date;Time;ID;F;F0;Fm;Fm\';Epar;Y(II);ETR;Fv/Fm;NPQ;deltaNPQ;rETR;Notes')
#


def open_files(data_path, ids_path, columns_path, output_path):
    print(data_path)
    with open(ids_path) as id_file:
        id_lines = id_file.readlines()

    with open(data_path) as raw_file:
        raw_lines = raw_file.readlines()

    # TODO: read the column names from the raw file to figure out their positions

    for id_line in id_lines:
        id_file_columns = id_line.split(";")
        if id_file_columns[0] != "\"Date\"":
            process_id_line(id_file_columns, raw_lines)


def main(argv):
    data_path = ''
    ids_path = ''
    columns_path = ''
    output_path = ''
    opts, args = getopt.getopt(argv, "d:i:c:o:", ["data=", "ids=", "columns=", "output="])
    for opt, arg in opts:
        if opt in ("-d", "--data"):
            data_path = arg
        elif opt in ("-i", "--ids"):
            ids_path = arg
        elif opt in ("-c", "--columns"):
            columns_path = arg
        elif opt in ("-o", "--output"):
            output_path = arg
    open_files(data_path, ids_path, columns_path, output_path)


if __name__ == "__main__":
    main(sys.argv[1:])
