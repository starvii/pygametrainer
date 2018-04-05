#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
大富翁4修改器
"""

from __future__ import with_statement, absolute_import, print_function
import sys

VER = sys.version_info.major
if VER < 3:
    range = xrange
from multiprocessing.dummy import Process
import time
from win32api import API, Instance


class Game:
    BinaryName = 'rich4.exe'

    class Basic:
        cash = 0x96B84, 4
        deposit = 0x96B88, 4
        points = 0x96B98, 2
        inflate_rate = 0x990E8, 2

        @staticmethod
        def angel(instance):
            addr = instance.base + Game.Basic.points[0]
            return instance.write(addr, 300, 2)

    class Item:
        machine_doll = 0x9915C, 1
        barrier = 0x9915D, 1
        mine = 0x9915E, 1
        timing_bomb = 0x9915F, 1
        motorcycle = 0x99160, 1
        car = 0x99161, 1
        missile = 0x99162, 1
        remote_control_dice = 0x99163, 1
        robot_worker = 0x99164, 1
        time_machine = 0x99165, 1
        conveyer = 0x99166, 1
        engineering_vehicle = 0x99167, 1
        nuclear_missile = 0x99168, 1

        @staticmethod
        def angel(instance):
            b = instance.base
            t = Game.Item
            c = 200
            ret = instance.write(b + t.machine_doll[0], c)
            if not ret: return False
            ret = instance.write(b + t.barrier[0], c)
            if not ret: return False
            ret = instance.write(b + t.mine[0], c)
            if not ret: return False
            ret = instance.write(b + t.timing_bomb[0], c)
            if not ret: return False
            ret = instance.write(b + t.motorcycle[0], c)
            if not ret: return False
            ret = instance.write(b + t.car[0], c)
            if not ret: return False
            ret = instance.write(b + t.missile[0], c)
            if not ret: return False
            ret = instance.write(b + t.remote_control_dice[0], c)
            if not ret: return False
            ret = instance.write(b + t.robot_worker[0], c)
            if not ret: return False
            ret = instance.write(b + t.time_machine[0], c)
            if not ret: return False
            ret = instance.write(b + t.conveyer[0], c)
            if not ret: return False
            ret = instance.write(b + t.engineering_vehicle[0], c)
            if not ret: return False
            ret = instance.write(b + t.nuclear_missile[0], c)
            if not ret: return False
            return True

    class Card:
        card_base = 0x99120
        card_pool = 0x99197
        card_set = set([0x03, 0x07, 0x09, 0x0d, 0x13, 0x14, 0x15, 0x16])  # 期望应有的卡片

        @staticmethod
        def add_card(instance, card_id):
            addr = instance.base + Game.Card.card_pool + card_id
            card_num = instance.read(addr)
            card_num -= 1
            instance.write(addr, card_num)

        @staticmethod
        def remove_card(instance, card_id):
            addr = instance.base + Game.Card.card_pool + card_id
            card_num = instance.read(addr)
            card_num += 1
            instance.write(addr, card_num)

        @staticmethod
        def angel(instance):
            addr = instance.base + Game.Card.card_base
            buf = API.read(instance.handle, addr, 15)
            my_cards = set()
            cl = list()
            to_remove = list()
            for c in buf:
                if c > 0:
                    if c in my_cards:
                        to_remove.append(c)  # 重复的卡片
                    else:
                        cl.append(c)
                        my_cards.add(c)  # 现有的卡片
            assert len(cl) == len(my_cards)

            cards = Game.Card.card_set
            to_add = cards.difference(my_cards)  # 缺少的期望卡片
            if len(to_add) > 0:  # 缺少。应当补充
                if len(to_add) + len(my_cards) > 15:  # 如果现有卡片加上应有卡片超标的话
                    to_remove_size = len(to_add) + len(my_cards) - 15  # 多出的张数
                    over = my_cards.difference(cards)  # 多余的卡片
                    for _ in range(to_remove_size):
                        card_id = over.pop()  # 随机删除一些多余的卡片
                        cl.remove(card_id)
                        to_remove.append(card_id)
                cl.extend(to_add)
                assert len(cl) <= 15
            bf = bytearray(cl).ljust(15, b'\x00')
            for c in to_remove:
                Game.Card.remove_card(instance, c)
            for c in to_add:
                Game.Card.add_card(instance, c)
            if bf != buf:
                API.write(instance.handle, addr, bf)

            return True

    class Immortal:
        # TODO: 神明
        pass


def angel():
    while 1:
        t = API.find_process_by_name(Game.BinaryName)
        if not t:
            print('cannot find process: {}.'.format(Game.BinaryName))
            time.sleep(1)
            continue
        pid, bn = t
        print('find pid: {}'.format(pid))
        t = API.find_module_by_name(pid, bn)
        if not t:
            time.sleep(1)
            continue
        base, _ = t
        print('module base: {}'.format(hex(base)))
        t = API.open_process(pid)
        if not t:
            print('cannot find module base: {}.'.format(Game.BinaryName))
            time.sleep(1)
            continue
        instance = Instance(t, base)
        while 1:
            if not Game.Basic.angel(instance):
                break
            if not Game.Item.angel(instance):
                break
            Game.Card.angel(instance)
            time.sleep(0.5)


def main():
    p = Process(target=angel)
    p.daemon = True
    p.start()
    input('press any key to exit ...')


if __name__ == '__main__':
    main()
