from sqlite3 import connect
from datetime import date
import locale
from calendar import monthrange

locale.setlocale(locale.LC_ALL, 'deu_deu')

def make_currency_format(input_list):
    """Wandelt alle Integer-Werte in einer Liste ins Währungsformat um"""
    output_list = []
    for item in input_list:
        if type(item) == int or type(item) == float:
            output_list.append(locale.currency(item, grouping=True))
        else:
            output_list.append(item)
    return output_list
    
def make_table_line(input_list, header_flag):
    """wandelt eine Liste in eine HTML-Tabellenzeile um. Wenn das Flag sesetzt ist, wird eine Kopfzeile erzeugt."""
    tag_str_open = "<td>"
    tag_str_close = "</td>"
    if header_flag:
        tag_str_open = "<th>"
        tag_str_close = "</th>"
    output_string = "<tr>"
    for item in input_list:
        output_string += tag_str_open + item + tag_str_close
    output_string += "</tr>"
    return output_string + "\n"


# Datenbankverbindung öffnen
db_conn = connect('C:\\Users\\Mike Dannenberg\\Documents\\Django\\testproject\\jangy_site\\db.sqlite3')
db_cursor = db_conn.cursor()
db_cursor2 = db_conn.cursor()

month = 5
year = 2016

days_in_month = monthrange(year, month)[1]

firstday = date(year, month, 1).strftime('%Y-%m-%d')
lastday = date(year, month, days_in_month).strftime('%Y-%m-%d')
month_text = date(year, month, 1).strftime('%B')

# SQL Statement für Ausgaben erzeugen
statement = "select belegdatum, sum(betrag) from steuer_ausgaben where belegdatum between "
statement += "'" + firstday + "' and '" + lastday + "'" 
statement += " group by belegdatum order by belegdatum;"

# print(statement)
result = db_cursor.execute(statement)

# SQL Statement für Einnahmen erzeugen

statement = "select tagesdatum, brutto_mwst1, brutto_mwst2 from steuer_einnahmen where tagesdatum between "
statement += "'" + firstday + "' and '" + lastday + "';"

# print(statement)
result_sales = db_cursor2.execute(statement)

# Dictonary für den Report
report_dict = {}

# Aufbau des Reports:
#   Datum
#   Wochentag
#   Ausgaben
#   Einnahmen mwSt1
#   Einnahmen MwSt2
#   Einahmen gesamt
#   Einnahmen - Ausgaben
#   Bestand

# Initialisierung - für jeden Tag des Monats wird ein leerer Eintrag im Report Dict angelegt.
for day in range(1, days_in_month + 1):
    report_date = date(year, month, day)
    report_dict[day] = [report_date.strftime('%x'), report_date.strftime('%a'), 0, 0, 0]
    
# Eintragen der Ausgaben - dort wo ein Wert vorhanden ist, wird der Default im Report Dict
# (0,00 €) durch den Wert aus der DB ersetzt. Dabei wird der Deziamltrenner geändert und es
# wird gerundet, das das Ergebnis aus der DB Rundungsfahler aufweist.
# print("Ausgaben")
for my_row in result:
    # print(str(my_row))
    result_day = int(my_row[0][8:10])
    report_dict[result_day][2] = round(my_row[1],2)

# Eintragen der Werte für die Einnahmen
# print("Einnahmen")
for my_row in result_sales:
    # print(str(my_row))
    result_day = int(my_row[0][8:10])
    report_dict[result_day][3] = round(my_row[1], 2)
    report_dict[result_day][4] = round(my_row[2], 2)

# Weitere Berechnungen
sum_exp = 0
sum_sale1 = 0
sum_sale2 = 0
sum_sale_all = 0
diff_sale_exp = 0
balance = 0 
for report_day, day_list in report_dict.items():    
    # Summe der Einahmen (MwSt1 und MwSt2) pro Tag
    sum_sale_day = day_list[3] + day_list[4]
    day_list.append(sum_sale_day)
    # Einahmen minus Ausgaben pro Tag
    diff_sale_exp_day = day_list[5] - day_list[2]
    day_list.append(diff_sale_exp_day)
    # Bestand fortlaufend
    balance += day_list[6]
    day_list.append(balance)
    # Summe der Ausgaben fortlaufend
    sum_exp += day_list[2]
    # Summe der Einahmen fortlaufend
    # Mwst1
    sum_sale1 += day_list[3]
    # MwSt2
    sum_sale2 += day_list[4]
    # Gesamt
    sum_sale_all += sum_sale_day
    # Einnahmen - AUsgaben
    diff_sale_exp += diff_sale_exp_day
    
# Ausgabe des Reports

# Liste der Spaltennamen
header_list = ["Datum", "Wochentag", "Ausgaben", "Einnahmen <br>MwSt1", "Einnahmen <br>MwSt2", "Einahmen <br>gesamt", "Einnahmen - <br>Ausgaben", "Bestand"]
  
# Ausgabedatei
out_path = "C:\\Users\\Mike Dannenberg\\Documents\\Django\\testproject\\jangy_site\\steuer\\data\\"
out_filename = "Report_" + str(month).zfill(2) + "_" + str(year) + ".html"
out_file = open(out_path + out_filename, 'w', encoding = 'utf-8')

out_file.write("<html lang='de'>\n<head>\n<meta charset='UTF-8'>\n")
out_file.write("<title>Natthanicha Thai Küche - Einnahmen und Augaben</title>\n")
out_file.write("<style>\ntable, th, td {border: 1px solid black; border-collapse: collapse;}\n")
out_file.write("th, td {padding: 0.3em; text-align: right; vertical-align: top}\n</style>\n")
out_file.write("</head>\n<body>\n")

out_file.write("<h1>Natthanicha Thai Küche - Einnahmen und Augaben</h1>")
out_file.write("<h2>" + month_text + " " + str(year) + "</h2>")

out_file.write("<table>")
out_file.write(make_table_line(header_list, True))

for report_day in report_dict.values():
    output_line = make_table_line(make_currency_format(report_day), False)
    out_file.write(output_line)

sum_line = ["Summe", " ", sum_exp, sum_sale1, sum_sale2, sum_sale_all, diff_sale_exp, balance]
out_file.write(make_table_line(make_currency_format(sum_line), False))

out_file.write("</table>\n</body>\n</html>\n")

out_file.close()
db_conn.close()
