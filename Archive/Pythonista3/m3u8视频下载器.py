#!/usr/bin/python3
# -*- coding: utf-8 -*-
# @File    : ppcxydow4m3u8-multi4ios.py
# @Author  : loli
# @Date    : 2018-03-25
# @Version : v6.66
# @Contact : https://t.me/weep_x
# @tg group: https://t.me/pythonista3dalaoqun

'''
多线程版for ios
下载m3u8直链并合并文件，支持手动合并
后续将支持断点续传
'''

import os
import sys
import contextlib
import uuid
import urllib.request, urllib.error, urllib.parse
import shutil
import appex, clipboard, re, console

import queue
import threading
import contextlib
import time

# 创建空对象,用于停止线程
StopEvent = object()


class ThreadPool:
    def __init__(self, max_num, max_task_num=None):
        """
        初始化线程池
        :param max_num: 线程池最大线程数量
        :param max_task_num: 任务队列长度
        """
        # 如果提供了最大任务数的参数，则将队列的最大元素个数设置为这个值。
        if max_task_num:
            self.q = queue.Queue(max_task_num)
        # 默认队列可接受无限多个的任务
        else:
            self.q = queue.Queue()
        # 设置线程池最多可实例化的线程数
        self.max_num = max_num
        # 任务取消标识
        self.cancel = False
        # 任务中断标识
        self.terminal = False
        # 已实例化的线程列表
        self.generate_list = []
        # 处于空闲状态的线程列表
        self.free_list = []

    def put(self, func, args, callback=None):
        """
        往任务队列里放入一个任务
        :param func: 任务函数
        :param args: 任务函数所需参数
        :param callback: 任务执行失败或成功后执行的回调函数，回调函数有两个参数
        1、任务函数执行状态；2、任务函数返回值（默认为None，即：不执行回调函数）
        :return: 如果线程池已经终止，则返回True否则None
        """
        # 先判断标识，看看任务是否取消了
        if self.cancel:
            return
        # 如果没有空闲的线程，并且已创建的线程的数量小于预定义的最大线程数，则创建新线程。
        if len(self.free_list) == 0 and len(self.generate_list) < self.max_num:
            self.generate_thread()
        # 构造任务参数元组，分别是调用的函数，该函数的参数，回调函数。
        w = (func, args, callback,)
        # 将任务放入队列
        self.q.put(w)

    def generate_thread(self):
        """
        创建一个线程
        """
        # 每个线程都执行call方法
        t = threading.Thread(target=self.call)
        t.start()

    def call(self):
        """
        循环去获取任务函数并执行任务函数。在正常情况下，每个线程都保存生存状态，
        直到获取线程终止的flag。
        """
        # 获取当前线程的名字
        current_thread = threading.currentThread().getName()
        # 将当前线程的名字加入已实例化的线程列表中
        self.generate_list.append(current_thread)
        # 从任务队列中获取一个任务
        event = self.q.get()
        # 让获取的任务不是终止线程的标识对象时
        while event != StopEvent:
            # 解析任务中封装的三个参数
            func, arguments, callback = event
            # 抓取异常，防止线程因为异常退出
            try:
                # 正常执行任务函数
                result = func(current_thread, *arguments)
                success = True
            except Exception as e:
                print(e)
                # 当任务执行过程中弹出异常
                result = None
                success = False
            # 如果有指定的回调函数
            if callback is not None:
                # 执行回调函数，并抓取异常
                try:
                    callback(success, result)
                except Exception as e:
                    pass
            # 当某个线程正常执行完一个任务时，先执行worker_state方法
            with self.worker_state(self.free_list, current_thread):
                # 如果强制关闭线程的flag开启，则传入一个StopEvent元素
                if self.terminal:
                    event = StopEvent
                # 否则获取一个正常的任务，并回调worker_state方法的yield语句
                else:
                    # 从这里开始又是一个正常的任务循环
                    event = self.q.get()
        else:
            # 一旦发现任务是个终止线程的标识元素，将线程从已创建线程列表中删除
            self.generate_list.remove(current_thread)

    def close(self):
        """
        执行完所有的任务后，让所有线程都停止的方法
        """
        # 设置flag
        self.cancel = True
        # 计算已创建线程列表中线程的个数，然后往任务队列里推送相同数量的终止线程的标识元素
        full_size = len(self.generate_list)
        while full_size:
            self.q.put(StopEvent)
            full_size -= 1

    def terminate(self):
        """
        在任务执行过程中，终止线程，提前退出。
        """
        self.terminal = True
        # 强制性的停止线程
        while self.generate_list:
            self.q.put(StopEvent)

    # 该装饰器用于上下文管理
    @contextlib.contextmanager
    def worker_state(self, state_list, worker_thread):
        """
        用于记录空闲的线程，或从空闲列表中取出线程处理任务
        """
        # 将当前线程，添加到空闲线程列表中
        state_list.append(worker_thread)
        # 捕获异常
        try:
            # 在此等待
            yield
        finally:
            # 将线程从空闲列表中移除
            state_list.remove(worker_thread)


pool = None

save_dir = os.path.expanduser('~/Documents/m3u8')
if not os.path.exists(save_dir):
    os.makedirs(save_dir)


def rm_file(file_path):
    if os.path.isfile(file_path):
        os.remove(file_path)
    elif os.path.exists(file_path):
        shutil.rmtree(file_path)


def mkdir(path):
    if not os.path.exists(path):
        os.mkdir(path)


def download(target_file, url):
    try:
        with contextlib.closing(urllib.request.urlopen(url)) as rs:
            handle = open(target_file, 'wb')
            handle.write(rs.read())
            handle.close()
            redirect_url = rs.geturl()
            return redirect_url
    except:
        print('资源连接失败，请检查链接有效性。')

    return url


READ_SIZE = 1024


def join_file(base_path, target_file):
    output = open(target_file, 'wb')
    files = os.listdir(base_path)
    files.sort()
    for file_name in files:
        file_path = os.path.join(base_path, str(file_name))
        file_obj = open(file_path, 'rb')
        while 1:
            file_bytes = file_obj.read(READ_SIZE)
            if not file_bytes:
                break
            output.write(file_bytes)
        file_obj.close()
    output.close()


def t_download(name, target_file, url):
    download(target_file, url)


def download_callback(status, result):
    """
    根据需要进行的回调函数，默认不执行。
    :param status: action函数的执行状态
    :param result: action函数的返回值
    :return:
    """
    if pool.cancel:
        print("正在回收资源：%d" % pool.q.qsize())
    elif pool.q.qsize() != 0:
        print("剩余下载数：%d" % pool.q.qsize())
    elif not pool.cancel:
        pool.close()
        print("资源下载完毕，正在处理合并，请稍等...")


def add_download(ts_name, ts_url):
    pool.put(t_download, (ts_name, ts_url), download_callback)


def download_m3u8(m3u8_url):
    current_m3u8 = str(uuid.uuid1());
    # 生成m3u8文件，采用uuid命名处理并发下载
    m3u8_file = '%s%s' % (current_m3u8, '.m3u8.tmp')
    logfile = '%s%s' % (current_m3u8, 'm3u8.log')
    rm_file(m3u8_file)
    print('正在解析m3u8资源: %s' % m3u8_url)
    redirect_next_url = download(m3u8_file, m3u8_url)

    if not os.path.exists(m3u8_file):
        return ''
    tem_ts_path = '%s%s' % (current_m3u8, 'ts')

    sum_ts = len(open(m3u8_file, 'rU').readlines())
    print('开始分析m3u8资源，资源总数: %d' % (sum_ts))

    with open(m3u8_file) as source:
        ts_index = 1

        mkdir(tem_ts_path)

        with open(logfile, 'w') as log:
            for line in source:

                _ts_url = line.strip()
                if _ts_url and len(_ts_url) > 1 and not _ts_url.startswith('#'):
                    ts_name = ('%s%s%04d.ts' % (tem_ts_path, os.sep, ts_index))
                    log.write(ts_name)
                    log.write('\n')
                    ts_url = urllib.parse.urljoin(redirect_next_url, _ts_url)
                    add_download(ts_name, ts_url)
                    ts_index += 1
                else:
                    log.write(line)

    while (pool.q.qsize() != 0):
        time.sleep(10)

    print('下载完成，正在合并.........')
    join_file(tem_ts_path, current_m3u8 + '.ts')
    print('合并完成,执行文件清理.........')
    rm_file(m3u8_file)
    rm_file(tem_ts_path)
    rm_file(logfile)
    new_file_name = console.input_alert('处理完毕，是否修改文件名？(不修改直接确定)：', '', current_m3u8)
    if new_file_name != '':
        os.rename(current_m3u8 + '.ts', os.path.join(save_dir, new_file_name + '.ts'))
    return new_file_name


def main():
    # 三种入口方式
    if appex.is_running_extension() and re.search('http*:\/\/[^\s]+', appex.get_attachments()[0]) is not None:
        url = appex.get_attachments()[0]
    else:
        clip = re.search('http*:\/\/[^\s]+', clipboard.get())

        if clip is None:
            url = console.input_alert('请输入m3u8资源地址：')
        else:
            url = clipboard.get()
    
        global pool

    pool_size = console.input_alert('请输入线程数，不输入默认5线程：', '', '5')

    if pool_size == '':
        pool_size = 5
    pool = ThreadPool(int(pool_size));
    
    new_file_name = download_m3u8(url)
    if new_file_name != '':
        print('================================')
        print('下载完毕，存储为 this phone/m3u8目录\n文件名:')
        print(new_file_name + '.ts')
        print('请使用支持ts格式播放器播放')
        print('================================')

#http://vip.okokbo.com/ppvod/8A0910F51B58C20F3715BDD82C350942.m3u8
if __name__ == "__main__":
    if len(sys.argv) >= 2 and sys.argv[1] != '':
        m3u8_file = '%s%s' % (sys.argv[1], '.m3u8.tmp')
        logfile = '%s%s' % (sys.argv[1], 'm3u8.log')
        tem_ts_path = '%s%s' % (sys.argv[1], 'ts')
        print('手动合并，正在合并.........')
        join_file(tem_ts_path, sys.argv[1] + '.ts')
        print('合并完成,执行文件清理.........')
        rm_file(m3u8_file)
        rm_file(tem_ts_path)
        rm_file(logfile)
        new_file_name = console.input_alert('处理完毕，是否修改文件名？(不修改直接确定)：', '', sys.argv[1])
        if new_file_name != '':
            os.rename(sys.argv[1] + '.ts', new_file_name + '.ts')
    else:
        main()
