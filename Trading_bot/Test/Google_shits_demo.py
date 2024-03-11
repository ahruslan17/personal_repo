# pip install gspread
import gspread
from oauth2client.service_account import ServiceAccountCredentials

json_keyfile_path = 'credentials.json'


# Установка области действия (Scope) и создание объекта ServiceAccountCredentials
scope = ['https://spreadsheets.google.com/feeds', 'https://www.googleapis.com/auth/drive']
credentials = ServiceAccountCredentials.from_json_keyfile_name(json_keyfile_path, scope)
gc = gspread.authorize(credentials)

# Вывести все доступные таблицы в аккаунте
for spreadsheet in gc.openall():
    print(spreadsheet.title)
#
# # Открытие таблицы по ее названию
spreadsheet_name = 'Копия Торговля на листинге фьючерсов (лог)'
worksheet = gc.open(spreadsheet_name).sheet1

# # Получение всех значений из таблицы
# data = worksheet.get_all_values()
#
# # Вывод содержимого таблицы
# for row in data:
#     print(row)

new_row = ['28.11.2023', 'MEME', '11:21', '6%', '15:00', '3%', '1.5%', '0.234', '0.256', 1.23, 0.211, 'нет', 'нет', 'да', '-1.5%', '1115']
worksheet.append_row(new_row)
