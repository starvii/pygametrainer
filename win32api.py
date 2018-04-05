#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import with_statement, absolute_import, print_function
import sys
VER = sys.version_info.major
if VER < 3:
    range = xrange
import struct
from ctypes import Structure, byref, sizeof, POINTER, windll, c_char
from ctypes.wintypes import DWORD, LONG, ULONG, MAX_PATH, HMODULE, BYTE, LPVOID, LPCVOID



"""

"""

USER32 = windll.LoadLibrary('user32')
KERNEL32 = windll.LoadLibrary('kernel32')

MAX_MODULE_NAME32 = 0xFF
TH32CS_SNAPPROCESS = 0x00000002
TH32CS_SNAPMODULE = 0x00000008
TH32CS_SNAPMODULE32 = 0x00000010
INVALID_HANDLE_VALUE = -1  # 0xFFFFFFFF
NULL = 0


PROCESS_VM_OPERATION = 0x0008
PROCESS_VM_READ = 0x0010
PROCESS_VM_WRITE = 0x0020
PROCESS_QUERY_INFORMATION = 0x0400

class PROCESSENTRY32(Structure):
    _fields_ = [
        ('dwSize', DWORD),
        ('cntUsage', DWORD),
        ('th32ProcessID', DWORD),
        ('th32DefaultHeapID', POINTER(ULONG)),
        ('th32ModuleID', DWORD),
        ('cntThreads', DWORD),
        ('th32ParentProcessID', DWORD),
        ('pcPriClassBase', LONG),
        ('dwFlags', DWORD),
        ('szExeFile', c_char * MAX_PATH),
    ]


class MODULEENTRY32(Structure):
    _fields_ = [
        ('dwSize', DWORD),
        ('th32ModuleID', DWORD),
        ('th32ProcessID', DWORD),
        ('GlblcntUsage', DWORD),
        ('ProccntUsage', DWORD),
        ('modBaseAddr', LPVOID),
        ('modBaseSize', DWORD),
        ('hModule', HMODULE),
        ('szModule', c_char * (MAX_MODULE_NAME32 + 1)),
        ('szExePath', c_char * MAX_PATH),
    ]


class API:

    @staticmethod
    def find_process_by_name(exe_name):
        """
        as the method name.
        :param exe_name: exe name
        :return: (pid, exe_name)
        """
        result = None
        en = (exe_name if VER < 3 else exe_name.encode()).upper()
        procSnap = KERNEL32.CreateToolhelp32Snapshot(TH32CS_SNAPPROCESS, 0)
        if procSnap == INVALID_HANDLE_VALUE or procSnap == NULL:
            print('CreateToolhelp32Snapshot failed: {}.'.format(KERNEL32.GetLastError()))
        pe32 = PROCESSENTRY32()
        pe32.dwSize = sizeof(PROCESSENTRY32)
        ret = KERNEL32.Process32First(procSnap, byref(pe32))
        if not ret:
            print('Process32First failed: {}.'.format(KERNEL32.GetLastError()))
        while ret:
            if en == pe32.szExeFile.upper():
                result = (pe32.th32ProcessID, pe32.szExeFile if VER < 3 else pe32.szExeFile.decode())
                break
            ret = KERNEL32.Process32Next(procSnap, byref(pe32))
        KERNEL32.CloseHandle(procSnap)
        return result
    
    @staticmethod
    def find_module_by_name(pid, module_name):
        """
        as the method name.
        :param pid: process ID
        :param module_name: exe name
        :return: (module base address, module full path)
        """
        result = None
        en = (module_name if VER < 3 else module_name.encode()).upper()
        modSnap = KERNEL32.CreateToolhelp32Snapshot(TH32CS_SNAPMODULE | TH32CS_SNAPMODULE32, pid)
        if modSnap == INVALID_HANDLE_VALUE or modSnap == NULL:
            print('CreateToolhelp32Snapshot failed: {}.'.format(KERNEL32.GetLastError()))
            # if LastError is 299 ... maybe you use pythonX86 but the process is X64?
            return
        me32 = MODULEENTRY32()
        me32.dwSize = sizeof(MODULEENTRY32)
        ret = KERNEL32.Module32First(modSnap, byref(me32))
        while ret:
            if en == me32.szModule.upper():
                result = (
                    me32.modBaseAddr,
                    me32.szExePath if VER < 3 else me32.szExePath.decode()
                )
                break
            ret = KERNEL32.Module32Next(modSnap, byref(me32))
        KERNEL32.CloseHandle(modSnap)
        return result
    
    @staticmethod
    def find_process_by_class_or_caption(class_name, caption):
        """
        :param class_name: the 1st param in WIN32 API FindWindow
        :param caption: the 2nd param in WIN32 API FindWindow
        :return: process ID
        """
        hwnd = USER32.FindWindow(class_name, caption)
        if hwnd == NULL:
            return INVALID_HANDLE_VALUE
        pid = DWORD()
        ret = USER32.GetWindowThreadProcessId(hwnd, byref(pid))
        if not ret:
            return NULL
        return pid

    @staticmethod
    def open_process(pid):
        hprc = KERNEL32.OpenProcess(PROCESS_VM_OPERATION | PROCESS_VM_READ | PROCESS_VM_WRITE, False, pid)
        if hprc != INVALID_HANDLE_VALUE or hprc != NULL:
            return hprc
        else:
            print('OpenProcess failed: {}.'.format(KERNEL32.GetLastError()))

    @staticmethod
    def close_handle(handle):
        KERNEL32.CloseHandle(handle)

    @staticmethod
    def read(hprc, addr, length):
        """
        read process memory
        :param hprc: process handle
        :param addr: memory address
        :param length: data length
        :return: buffer in bytes
        """
        BUFFER = BYTE * length
        buf = BUFFER()
        p = LPCVOID(addr)
        read_size = DWORD()
        ret = KERNEL32.ReadProcessMemory(hprc, p, buf, length, byref(read_size))
        if not ret:
            print('ReadProcessMemory failed: {}.'.format(KERNEL32.GetLastError()))
            return
        if read_size.value != length:
            print('ReadProcessMemory read_size error.')
            return
        # for b in buf:
        #     print(b,)
        data = bytearray(buf)
        return data

    
    @staticmethod
    def write(hprc, addr, buffer):
        """
        Write process memory
        :param hprc: process handle
        :param addr: memory address
        :param buffer: buffer in bytes
        :return: write size
        """
        assert type(buffer) == bytearray or bytes
        length = len(buffer)
        BUFFER = BYTE * length
        buf = BUFFER()
        for i, b in enumerate(buffer):
            assert 0 <= b <= 0xFF
            buf[i] = b
        p = LPCVOID(addr)
        write_size = DWORD()
        ret = KERNEL32.WriteProcessMemory(hprc, p, buf, length, byref(write_size))
        if not ret:
            print('WriteProcessMemory failed: {}.'.format(KERNEL32.GetLastError()))
            return
        if write_size.value != length:
            print('WriteProcessMemory write_size error.')
            return
        return write_size.value


class Instance:
    byte = 1
    word = 2
    dword = 4
    qword = 8


    def __init__(self, hprc, image_base):
        self.handle = hprc
        self.base = image_base


    def read(self, addr, type=byte):
        assert type in (Instance.byte, Instance.word, Instance.dword, Instance.qword)
        buf = API.read(self.handle, addr, type)
        assert len(buf) == type
        buf = buf.ljust(8, b'\x00')
        return struct.unpack('@Q', buf)[0]

    def write(self, addr, data, type=byte):
        assert type in (Instance.byte, Instance.word, Instance.dword, Instance.qword)
        if type == Instance.byte:
            assert 0 <= data <= 0xFF
            buf = bytearray([data])
        elif type == Instance.word:
            assert 0 <= data <= 0xFFFF
            buf = struct.pack('@H', data)
        elif type == Instance.dword:
            assert 0 <= data <= 0xFFFFFFFF
            buf = struct.pack('@I', data)
        else:
            assert 0 <= data <= 0xFFFFFFFFFFFFFFFF
            buf = struct.pack('@Q', data)
        if VER < 3:
            buf = bytearray(buf)
        return API.write(self.handle, addr, buf)


# def _test():
#     r = API.find_process_by_name('plagueincevolved.exe')
#     print(r)
#     if not r:
#         return
#     pid, name = r
#     r = API.find_module_by_name(pid, name)
#     print(r)
#     g = Instance(pid)
#     buf = API.read(g.procHandle, 0x52B5755C, 4)
#     print(repr(buf))
#     buf = b'\x01\x01\x00\x00'
#     s = API.write(g.procHandle, 0x52B5755C, buf)
#     print(s)
#     print(g.read_dword(0x52B5755C))
#     g.close()


# if __name__ == '__main__':
#     _test()
