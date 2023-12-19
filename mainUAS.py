from http import HTTPStatus
from flask import Flask, request, abort
from flask_restful import Resource, Api
from models import Gitar as GitarModel
from engine import engine
from sqlalchemy import select
from sqlalchemy.orm import Session
from tabulate import tabulate

session = Session(engine)

app = Flask(__name__)
api = Api(app)


class BaseMethod():

    def __init__(self):
        self.raw_weight = {'nama_gitar': 3, 'merk': 4,
                           'berat_gitar': 3, 'body_material': 4, 'scale_length': 5, 'tipe':5, 'harga': 5}

    @property
    def weight(self):
        total_weight = sum(self.raw_weight.values())
        return {k: round(v/total_weight, 2) for k, v in self.raw_weight.items()}

    @property
    def data(self):
        query = select(GitarModel.no, GitarModel.nama_gitar, GitarModel.merk, GitarModel.berat_gitar, GitarModel.body_material,
                       GitarModel.scale_length, GitarModel.tipe, GitarModel.harga)
        result = session.execute(query).fetchall()
        print(result)
        return [{'no': Gitar.no, 'nama_gitar': Gitar.nama_gitar, 'merk': Gitar.merk, 'berat_gitar': Gitar.berat_gitar,
                'body_material': Gitar.body_material, 'scale_length': Gitar.scale_length, 'tipe': Gitar.tipe, 'harga': Gitar.harga} for Gitar in result]

    @property
    def normalized_data(self):
        # x/max [benefit]
        # min/x [cost]
        merk_values = []  # max
        berat_gitar_values = []  # max
        body_material_values = []  # max
        scale_length_values = []  # max
        tipe_values = [] # max
        harga_values = []  # min

        for data in self.data:
            # Merk
            merk_spec = data['merk']
            numeric_values = [int(value.split()[0]) for value in merk_spec.split(
                ',') if value.split()[0].isdigit()]
            max_merk_value = max(numeric_values) if numeric_values else 1
            merk_values.append(max_merk_value)

            # Berat Gitar
            berat_gitar_spec = data['berat_gitar']
            berat_gitar_numeric_values = [int(
                value.split()[0]) for value in berat_gitar_spec.split() if value.split()[0].isdigit()]
            max_berat_gitar_value = max(
                berat_gitar_numeric_values) if berat_gitar_numeric_values else 1
            berat_gitar_values.append(max_berat_gitar_value)

            # Body Material
            body_material_spec = data['body_material']
            body_material_numeric_values = [float(value.split()[0]) for value in body_material_spec.split(
            ) if value.replace('.', '').isdigit()]
            max_body_material_value = max(
                body_material_numeric_values) if body_material_numeric_values else 1
            body_material_values.append(max_body_material_value)

            # Scale Length
            scale_length_spec = data['scale_length']
            scale_length_numeric_values = [
                int(value) for value in scale_length_spec.split() if value.isdigit()]
            max_scale_length_value = max(
                scale_length_numeric_values) if scale_length_numeric_values else 1
            scale_length_values.append(max_scale_length_value)

            # Tipe
            tipe_spec = data['tipe']
            tipe_numeric_values = [
                int(value) for value in tipe_spec.split() if value.isdigit()]
            max_tipe_value = max(
                tipe_numeric_values) if tipe_numeric_values else 1
            tipe_values.append(max_tipe_value)

            # Harga
            harga_cleaned = ''.join(char for char in str(data['harga']) if char.isdigit())
            harga_values.append(int(harga_cleaned) if harga_cleaned else 0)  # Convert to integer


        return [
            {'no': data['no'],
             'merk': merk_value / max(merk_values),
             'berat_gitar': berat_gitar_value / max(berat_gitar_values),
             'body_material': body_material_value / max(body_material_values),
             'scale_length': scale_length_value / max(scale_length_values),
             'tipe': tipe_value / max(tipe_values),
             # To avoid division by zero
             'harga': min(harga_values) / max(harga_values) if max(harga_values) != 0 else 0
             }
            for data, merk_value, berat_gitar_value, body_material_value, scale_length_value, tipe_value, harga_value
            in zip(self.data, merk_values, berat_gitar_values, body_material_values, scale_length_values, tipe_values, harga_values)
        ]

    def update_weights(self, new_weights):
        self.raw_weight = new_weights


class WeightedProductCalculator(BaseMethod):
    def update_weights(self, new_weights):
        self.raw_weight = new_weights

    @property
    def calculate(self):
        normalized_data = self.normalized_data
        produk = [
            {
                'no': row['no'],
                'produk': row['merk']**self.weight['merk'] *
                row['berat_gitar']**self.weight['berat_gitar'] *
                row['body_material']**self.weight['body_material'] *
                row['scale_length']**self.weight['scale_length'] *
                row['tipe']**self.weight['tipe'] *
                row['harga']**self.weight['harga']
            }
            for row in normalized_data
        ]
        sorted_produk = sorted(produk, key=lambda x: x['produk'], reverse=True)
        sorted_data = [
            {
                'ID': product['no'],
                'score': round(product['produk'], 3)
            }
            for product in sorted_produk
        ]
        return sorted_data

class WeightedProduct(Resource):
    def get(self):
        calculator = WeightedProductCalculator()
        result = calculator.calculate
        return sorted(result, key=lambda x: x['score'], reverse=True), HTTPStatus.OK.value

    def post(self):
        new_weights = request.get_json()
        calculator = WeightedProductCalculator()
        calculator.update_weights(new_weights)
        result = calculator.calculate
        return {'gitar': sorted(result, key=lambda x: x['score'], reverse=True)}, HTTPStatus.OK.value


class SimpleAdditiveWeightingCalculator(BaseMethod):
    @property
    def calculate(self):
        weight = self.weight
        result = [
            {
                'ID': row['no'],
                'Score': round(row['merk'] * weight['merk'] +
                               row['berat_gitar'] * weight['berat_gitar'] +
                               row['body_material'] * weight['body_material'] +
                               row['scale_length'] * weight['scale_length'] +
                               row['tipe'] * weight['tipe'] +
                               row['harga'] * weight['harga'], 3)
            }
            for row in self.normalized_data
        ]
        sorted_result = sorted(result, key=lambda x: x['Score'], reverse=True)
        return sorted_result

    def update_weights(self, new_weights):
        self.raw_weight = new_weights


class SimpleAdditiveWeighting(Resource):
    def get(self):
        saw = SimpleAdditiveWeightingCalculator()
        result = saw.calculate
        return sorted(result, key=lambda x: x['Score'], reverse=True), HTTPStatus.OK.value

    def post(self):
        new_weights = request.get_json()
        saw = SimpleAdditiveWeightingCalculator()
        saw.update_weights(new_weights)
        result = saw.calculate
        return {'gitar': sorted(result, key=lambda x: x['Score'], reverse=True)}, HTTPStatus.OK.value


class Gitar(Resource):
    def get_paginated_result(self, url, list, args):
        page_size = int(args.get('page_size', 10))
        page = int(args.get('page', 1))
        page_count = int((len(list) + page_size - 1) / page_size)
        start = (page - 1) * page_size
        end = min(start + page_size, len(list))

        if page < page_count:
            next_page = f'{url}?page={page+1}&page_size={page_size}'
        else:
            next_page = None
        if page > 1:
            prev_page = f'{url}?page={page-1}&page_size={page_size}'
        else:
            prev_page = None

        if page > page_count or page < 1:
            abort(404, description=f'Data Tidak Ditemukan.')
        return {
            'page': page,
            'page_size': page_size,
            'next': next_page,
            'prev': prev_page,
            'Results': list[start:end]
        }

    def get(self):
        query = session.query(GitarModel).order_by(GitarModel.no)
        result_set = query.all()
        data = [{'no': row.no, 'nama_gitar': row.nama_gitar, 'merk': row.merk, 'berat_gitar': row.berat_gitar,
                 'body_material': row.body_material, 'scale_length': row.scale_length, 'tipe': row.tipe, 'harga': row.harga}
                for row in result_set]
        return self.get_paginated_result('gitar/', data, request.args), 200


api.add_resource(Gitar, '/gitar')
api.add_resource(WeightedProduct, '/wp')
api.add_resource(SimpleAdditiveWeighting, '/saw')

if __name__ == '__main__':
    app.run(port='5005', debug=True)