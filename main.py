import sys
from colorama import Fore, Style
from models import Base, gitar
from engine import engine
from tabulate import tabulate

from sqlalchemy import select
from sqlalchemy.orm import Session
from settings import DEV_SCALE

session = Session(engine)


def create_table():
    Base.metadata.create_all(engine)
    print(f'{Fore.GREEN}[Success]: {Style.RESET_ALL}Database has created!')


def review_data():
    query = select(gitar)
    for gitar in session.scalars(query):
        print(gitar)


class BaseMethod():

    def __init__(self):
        # 1-5
        self.raw_weight = {'merk': 3, 'berat_gitar': 4,'body_material': 4, 'scale_length': 5, 'type': 2, 'harga': 5}

    @property
    def weight(self):
        total_weight = sum(self.raw_weight.values())
        return {k: round(v/total_weight, 2) for k, v in self.raw_weight.items()}

    @property
    def data(self):
        query = select(gitar.no, gitar.merk, gitar.berat_gitar, gitar.body_material, gitar.scale_length, gitar.tipe, gitar.harga)
        result = session.execute(query).fetchall()
        return [{'no': gitar.no, 'merk': gitar.merk, 'berat_gitar': gitar.berat_gitar, 'body_material': gitar.body_material,
                 'scale_length': gitar.scale_length, 'tipe': gitar.tipe, 'harga': gitar.harga} for gitar in result]

    @property
    def normalized_data(self):
        # x/max [benefit]
        # min/x [cost]
        merk_values = []  # max
        berat_gitar_values = []  # max
        body_material_values = []  # max
        scale_length_values = []  # max
        type_values = [] #max
        harga_values = []  # min

        for data in self.data:
            # merk
            merk_spec = data['merk']
            numeric_values = [int(value.split()[0]) for value in merk_spec.split(',') if value.split()[0].isdigit()]
            max_merk_value = max(numeric_values) if numeric_values else 1
            merk_values.append(max_merk_value)

            # berat_gitar
            berat_gitar_spec = data['baterai']
            berat_gitar_numeric_values = [int(
                value.split()[0]) for value in berat_gitar_spec.split() if value.split()[0].isdigit()]
            max_berat_gitar_value = max(
                berat_gitar_numeric_values) if berat_gitar_numeric_values else 1
            berat_gitar_values.append(max_berat_gitar_value)

            # body_material
            body_material_spec = data['body']
            body_material_numeric_values = [
                int(value) for value in body_material_spec.split() if value.isdigit()]
            max_body_material_value = max(
                body_material_numeric_values) if body_material_numeric_values else 1
            body_material_values.append(max_body_material_value)

            # scale_length
            scale_length = DEV_SCALE['scale'].get(data['scale'], 1)
            scale_length.append(scale_length)

            # type
            type_spec = data['tipe']
            type_numeric_values = [
                int(value) for value in type_spec.split() if value.isdigit()]
            max_type_value = max(
                type_numeric_values) if type_numeric_values else 1
            type_values.append(max_type_value)

            # Harga
            harga_cleaned = ''.join(
                char for char in data['harga'] if char.isdigit())
            scale_length.append(float(harga_cleaned)
                                if harga_cleaned else 0)  # Convert to float

        return [
            {'no': data['no'],
             'gitar': merk_value / max(merk_values),
             'berat_gitar': berat_gitar_value / max(berat_gitar_values),
             'ram': body_material_value / max(body_material_values),
             'memori': scale_length_value / max(scale_length_values),
             'type' : type_value / max(type_values),
             # To avoid division by zero
             'harga': min(harga_values) / max(harga_values) if max(harga_values) != 0 else 0
             }
            for data, merk_value, berat_gitar_value, body_material_value, scale_length_value, type_value, harga_value
            in zip(self.data, merk_values, berat_gitar_values, body_material_values, scale_length_values, type_values, harga_values)
        ]


class WeightedProduct(BaseMethod):
    @property
    def calculate(self):
        normalized_data = self.normalized_data
        produk = [
            {
                'no': row['no'],
                'produk': row['kamera']**self.weight['kamera'] *
                row['baterai']**self.weight['baterai'] *
                row['ram']**self.weight['ram'] *
                row['memori']**self.weight['memori'] *
                row['harga']**self.weight['harga']
            }
            for row in normalized_data
        ]
        sorted_produk = sorted(produk, key=lambda x: x['produk'], reverse=True)
        sorted_data = [
            {
                'no': product['no'],
                'kamera': product['produk'] / self.weight['kamera'],
                'baterai': product['produk'] / self.weight['baterai'],
                'ram': product['produk'] / self.weight['ram'],
                'memori': product['produk'] / self.weight['memori'],
                'harga': product['produk'] / self.weight['harga'],
                'score': product['produk']  # Nilai skor akhir
            }
            for product in sorted_produk
        ]
        return sorted_data


class SimpleAdditiveWeighting(BaseMethod):
    @property
    def calculate(self):
        weight = self.weight
        result = {row['no']:
                  round(row['kamera'] * weight['kamera'] +
                        row['baterai'] * weight['baterai'] +
                        row['ram'] * weight['ram'] +
                        row['memori'] * weight['memori'] +
                        row['harga'] * weight['harga'], 2)
                  for row in self.normalized_data
                  }
        sorted_result = dict(
            sorted(result.items(), key=lambda x: x[1], reverse=True))
        return sorted_result


def run_saw():
    saw = SimpleAdditiveWeighting()
    result = saw.calculate
    print(tabulate(result.items(), headers=['No', 'Score'], tablefmt='pretty'))


def run_wp():
    wp = WeightedProduct()
    result = wp.calculate
    headers = result[0].keys()
    rows = [
        {k: round(v, 4) if isinstance(v, float) else v for k, v in val.items()}
        for val in result
    ]
    print(tabulate(rows, headers="keys", tablefmt="grid"))


if __name__ == "__main__":
    if len(sys.argv) > 1:
        arg = sys.argv[1]

        if arg == 'create_table':
            create_table()
        elif arg == 'saw':
            run_saw()
        elif arg == 'wp':
            run_wp()
        else:
            print('command not found')
