import psycopg2
import time

conn = psycopg2.connect(
    database='exampledb',
    user='admin',
    password='root',
    host='database',  # используем имя сервиса
    port=5432  # порт базы данных PostgreSQL
)

cur = conn.cursor()

# Создание таблицы students
create_table_query = '''
    CREATE TABLE IF NOT EXISTS students (
        id SERIAL PRIMARY KEY,
        name VARCHAR(100),
        age INTEGER
    );
'''
cur.execute(create_table_query)


# Вставка нескольких записей в таблицу students
students_data = [
    ('John', 25),
    ('Jane', 22),
    ('Bob', 30)
]

insert_query = 'INSERT INTO students (name, age) VALUES (%s, %s);'

cur.executemany(insert_query, students_data)

# Подтверждение транзакции
conn.commit()

cur.execute('SELECT * FROM students')
rows = cur.fetchall()
for row in rows:
    print(row)

cur.close()
conn.close()

while True:
    print('Script is working')
    time.sleep(5)