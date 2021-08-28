import sqlalchemy
from sqlalchemy import MetaData, Table
from SQL_test_data import user_data_dict, tula_data_list
from pprint import pprint


class SqlDataPersons:
    def __init__(self, sql_name_database, user_data=None, person_data=None):
        self.user_data = user_data if user_data is not None else None
        self.person_data = person_data if person_data is not None else None
        self.engine = sqlalchemy.create_engine(sql_name_database)
        self.connection = self.engine.connect()
        self.metadata = MetaData(self.connection)

    def _find_column_in_table(self, table_name):
        t = Table(f"{table_name}", self.metadata, autoload=True)
        columns = [m.key for m in t.c]
        return columns

    def _person_in_table(self, cell_value, table_name):
        return self.connection.execute(f'''SELECT id FROM {table_name}
                                                    WHERE id='{cell_value}'
                                                ''').fetchall()

    def _insert_info(self, table_name, cell_list, value_insert):
        self.connection.execute(f'''INSERT INTO {table_name}({cell_list})
                           VALUES({value_insert});
                    ''')

    def _fill_data_to_table(self, user_dict, table_name):
        result = ''
        cells = ''
        if self._person_in_table(user_dict['id'], table_name):
            print(f"{user_dict['id']} существует внутри {table_name}")
            return None
        for cell in self._find_column_in_table(table_name):
            if user_dict.get(cell, None) is None:
                return None
            elif isinstance(user_dict.get(cell), int):
                result += f'{user_dict[cell]},'
            else:
                result += f"'{user_dict[cell]}',"
            cells += f'{cell},'
        self._insert_info(table_name, cells[0:-1], result[0:-1])
        print(f"{user_dict['id']} добавлен {table_name}")

    def _get_relation(self, person_id=None):
        if person_id is None:
            return self.connection.execute(f'''SELECT clientid,personid  FROM usersconnect
                                              WHERE clientid={self.user_data['id']}
                                            ''').fetchall()
        else:
            return self.connection.execute(f'''SELECT clientid,personid FROM usersconnect
                                              WHERE clientid={self.user_data['id']} AND personid={person_id}
                                            ''').fetchall()

    def _convert_to_line(self):
        acceptation_list = [elem[1] for elem in self._get_relation()]
        acceptation_list.append(self.user_data['id'])
        return ",".join(map(str, acceptation_list))

    def _get_without_relation(self):

        return self.connection.execute(f'''SELECT * FROM person
                                            WHERE id NOT IN ({self._convert_to_line()})                                    
                                ''').fetchall()

    def _convert_to_template(self, list_output):
        out_put_data = []
        for list in list_output:
            person_data = dict(
                lastname=list[1],
                firstname=list[2],
                id=list[0],
                personurl=list[3],
                age=list[4],
                sex=list[5],
                city=list[6],
                relation=list[7],
                closed=list[8]
            )
            out_put_data.append(person_data)
        return out_put_data

    def _purge(self, table_name):
        self.connection.execute(f'''DELETE FROM {table_name}''')
        print(f'Таблица {table_name} удалена')

    def fill_user_data(self):
        if self.user_data is None:
            print('подключите клиента к БД')
            return None
        self._fill_data_to_table(self.user_data, 'client')
        self._fill_data_to_table(self.user_data, 'person')

    def fill_person_data(self):
        if self.person_data is None:
            print('подключите пользователя к БД')
            return None
        for persons in self.person_data:
            self._fill_data_to_table(persons, 'person')

    def fill_relation(self, person_id):
        if not self._get_relation(person_id):
            self.connection.execute(f'''INSERT INTO usersconnect (clientid,personid)
                               VALUES({self.user_data['id']},{person_id})''')
            print(f"отношение {self.user_data['id']}--->{person_id} добавлено")
        else:
            print(f"отношение {self.user_data['id']}---{person_id} существует")

    def get_three_users(self):
        list_of_persons = self._get_without_relation()
        end_range = len(list_of_persons) if len(list_of_persons) < 3 else 3
        output_list = []
        for i in range(0, end_range):
            self.fill_relation(list_of_persons[i][0])
            output_data = dict(
                id=list_of_persons[i][0],
                name=f'{list_of_persons[i][2]} {list_of_persons[i][1]}',
                vk_url=list_of_persons[i][3],
                photos=list_of_persons[i][8]
            )
            output_list.append(output_data)
        print('Список выгружаемых пользователей для пересылки:')
        pprint(output_list)

        return output_list

    def get_existed_by_request(self, data_for_sql):
        """
        метода для определения существования в базе людей подходящих под запрос пользователя,
        чтобы не повторять запрос к VK по API
        :param data_for_sql: словарь, который представлен форматирвоанным запросом от пользователя
        :return:
        """

        data_str = f"city = '{data_for_sql['city']}' AND sex = {data_for_sql['sex']} " \
                   f"AND relation = {data_for_sql['relation']} " \
                   f"AND age BETWEEN {data_for_sql['age_from']} AND {data_for_sql['age_to']}" \
                   f" AND id NOT IN ({self._convert_to_line()})"

        result_request = self.connection.execute(f'''SELECT * FROM person
                                                    WHERE {data_str}
                                         ''').fetchall()

        return self._convert_to_template(result_request)


if __name__ == '__main__':
    sql_name = 'postgresql://vk_user:vk_user@localhost:5432/vk_database_users'
    database1 = SqlDataPersons(sql_name, user_data=user_data_dict, person_data=tula_data_list)
    database1.fill_user_data()
    database1.fill_person_data()

    # database1._purge('usersconnect')
    # database1.fill_relation(139430839)
    # database1.fill_relation(226648896)
    # database1.get_three_users()

    data_for_sql = dict(
        city='Тула',
        sex=1,
        relation=6,
        age_from=23,
        age_to=24
    )
    pprint(database1.get_existed_by_request(data_for_sql))
