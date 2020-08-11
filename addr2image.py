#!/usr/bin/python
#coding:utf-8

import lldb
# import commands
import optparse
import shlex
import re


# 获取ASLR偏移地址
def get_images():
    # 获取'image list -o'命令的返回结果
    imgs = []
    interpreter = lldb.debugger.GetCommandInterpreter()
    returnObject = lldb.SBCommandReturnObject()
    interpreter.HandleCommand('image list -o -b', returnObject)
    output = returnObject.GetOutput();
    # print(output)
    for i in re.findall(r"^\[(.*)\] (0x\w+?) (.*?)(\(.*?\))?$", output, re.M):
        imgs.append(i[2])
    return imgs

def addr_in_section(img, addr):
    interpreter = lldb.debugger.GetCommandInterpreter()
    returnObject = lldb.SBCommandReturnObject()
    cmd = 'section ' + img
    interpreter.HandleCommand(cmd, returnObject)
    output = returnObject.GetOutput();
    # print(output)

    addr = int(addr, 16)
    for i in  re.findall(r"^\[(.*?)-(.*?)\] (.*?) (.*?)$", output, re.M):
        # print(i)
        start_addr = int(i[0], 16)
        stop_addr = int(i[1], 16)
        if addr - start_addr >= 0 and stop_addr - addr >= 0:
            return "[{}-{}] {} {}".format(i[0], i[1], i[2], i[3])
    return False


# Super breakpoint
def addr2image(debugger, command, result, internal_dict):

    #用户是否输入了地址参数
    if not command:
        print(result, 'Please input the address!')
        return

    images = get_images()
    if len(images):
        #如果找到了ASLR偏移，就设置断点
        for img in images:
            ret = addr_in_section(img, command)
            if ret:
                print('image: ', ret)
    else:
        print(result, 'images not found!')

# And the initialization code to add your commands 
def __lldb_init_module(debugger, internal_dict):
    # 'command script add addr2image' : 给lldb增加一个'addr2image'命令
    # '-f addr2image.addr2image' : 该命令调用了sbr文件的sbr函数
    debugger.HandleCommand('command script add addr2image -f addr2image.addr2image')
    print('The "addr2image" python command has been installed and is ready for use.')