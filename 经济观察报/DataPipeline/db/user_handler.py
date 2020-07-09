# coding: utf-8
import re
import time

import aliyun_db

API_SERVER = '127.0.0.1'
API_PORT = 6789


class UserHandler(object):
    def __init__(self):
        # self.table_cli = aliyun_db.get_unofficial_product_cli()
        self.table_cli = aliyun_db.get_unofficial_test_cli()

    def write_user(self, data):
        user_info = self.query_user(data)
        if user_info is None:
            self.put_user(data)
        else:
            print('Enter update')
            self.update_user(data, user_info)

    def put_user(self, data):
        """
        Put not exsit user info into database.

        :param data [dict]: User info dict.
            example:
                {
                    "medium_name": "财新",
                    "medium_id": 123,
                    "mp_type_id": 1,
                    "mp_type_name": '今日头条',
                    "mp_user_name": "财新网",
                    "mp_user_id": "1a3f92a3bc",
                    "logo": "https://gw.alipayobjects.com/zos/rmsportal/XuVpGqBFxXplzvLjJBZB.svg",
                    "intro": "用户介绍",
                    "fans_count": 100
                }
        """
        prepared_data = {
            'medium_id': data['medium_id'],
            'medium_name': data['medium_name'],
            'id': None,
            'mp_type_id': data['mp_type_id'],
            'mp_type_name': data['mp_type_name'],
            'name': data['mp_user_name'],
            'mp_user_id': data['mp_user_id'],
            'mp_user_medium_id': data.get('mp_user_medium_id', ''),
            'logo': data['logo'],
            'intro': re.sub(r'(?:\n| |)', '', data['intro']),
            'status': self.should_link_user(data),
            'fans_count': data['fans_count'],
            'created_at': int(time.time()),
            'updated_at': int(time.time()),
        }
        self.table_cli.put_row(table_name='mp_account',
                               pk_list=['medium_id', 'id'],
                               data=prepared_data)
        if prepared_data['status'] == 1:
            medium_data = self.query_medium(prepared_data['medium_id'])
            if medium_data:
                logo = medium_data.get('logo_url', '')
                intro = medium_data.get('introduction', '')
                if not logo or not intro or 'sina' in logo:
                    medium_data[
                        'logo_url'] = logo if logo else prepared_data['logo']
                    if 'sina' in logo:
                        medium_data['logo_url'] = prepared_data['logo']
                    medium_data[
                        'introduction'] = intro if intro else prepared_data[
                            'intro']
                    self.table_cli.update_row(table_name='medium',
                                              pk_list=['random_num', 'id'],
                                              data=medium_data)

    def update_user(self, data, user_info):
        """
        Update user info if user exists.

        :param data [dict]: user info data, get from spider.
        :param internal_id [int]: id field in table `mp_account`.
        """
        logo = user_info.get('logo', '')
        if not logo or 'sinaimg.cn' in logo:
            logo = data.get('logo', '')
        prepared_data = {
            'medium_id':
            data['medium_id'],
            'id':
            user_info['id'],
            'name':
            data['mp_user_name'],
            'logo':
            logo,
            'intro':
            user_info.get('intro', '')
            if user_info.get('intro', '') else data['intro'],
            'fans_count':
            data['fans_count'],
            'updated_at':
            int(time.time())
        }
        if data['medium_name'] == data['mp_user_name']:
            prepared_data['status'] = 1
        print(prepared_data)
        self.table_cli.update_row(table_name='mp_account',
                                  pk_list=['medium_id', 'id'],
                                  data=prepared_data)
        if user_info['status'] == 1:
            medium_data = self.query_medium(prepared_data['medium_id'])
            if medium_data:
                logo = medium_data.get('logo_url', '')
                intro = re.sub(r'(?:\n| |)', '',
                               medium_data.get('introduction', ''))
                if not logo or not intro or 'sinaimg.cn' in logo:
                    medium_data[
                        'logo_url'] = logo if logo else prepared_data['logo']
                    if 'sinaimg.cn' in logo:
                        medium_data['logo_url'] = prepared_data['logo']
                    medium_data['introduction'] = intro if intro else re.sub(
                        r'(?:\n| |)', '', data['intro'])
                    self.table_cli.update_row(table_name='medium',
                                              pk_list=['random_num', 'id'],
                                              data=medium_data)

    def should_link_user(self, data):
        """
        Check if mp_user_name is the same as mediium_name.

        :param data [dict]: user info data, get from spider.
        """
        print(data['medium_name'], data['mp_user_name'])
        print('-----------------------------------')
        return 1 if data['medium_name'] == data['mp_user_name'] else 2

    def query_mp_type_name(self, data):
        return ''

    def query_user(self, data):
        """
        Query user in table `mp_account`.

        :param mp_user_id [str]: User id at the platform.
        :return : user data in table `mp_account` if user exist else None.
        """
        mp_user_id = data['mp_user_id']
        must_query = [
            ('term', 'mp_user_id', mp_user_id),
        ]
        result_iter = self.table_cli.query('mp_account',
                                           must_query_list=must_query,
                                           index_name='mp_account_index')
        for mp in result_iter:
            return mp
        return

    def query_medium(self, medium_id):
        """
        Query user in table `mp_account`.

        :param mp_user_id [str]: User id at the platform.
        :return : user data in table `mp_account` if user exist else None.
        """
        must_query = [
            ('term', 'id', medium_id),
        ]
        result_iter = self.table_cli.query('medium',
                                           must_query_list=must_query,
                                           index_name='medium_index')
        for md in result_iter:
            return md
        return
