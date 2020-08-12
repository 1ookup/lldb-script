#!/usr/bin/python
#coding:utf-8
# 依赖 dslldb.py
import lldb
# import commands
import optparse
import shlex
import re
import os
import json

DUMP_PATH = "/tmp/images"

def get_images():
    imgs = []
    interpreter = lldb.debugger.GetCommandInterpreter()
    returnObject = lldb.SBCommandReturnObject()
    interpreter.HandleCommand('image list -o -b', returnObject)
    output = returnObject.GetOutput();
    # print(output)
    for i in re.findall(r"^\[(.*)\] (0x\w+?) (.*?)(\(.*?\))?$", output, re.M):
        imgs.append(i[2])
    return imgs

def dump_image(img):
    image_info = {}
    interpreter = lldb.debugger.GetCommandInterpreter()
    returnObject = lldb.SBCommandReturnObject()
    cmd = 'section ' + img
    interpreter.HandleCommand(cmd, returnObject)
    output = returnObject.GetOutput();
    pattern = r'\x1b\[\d+m';
    output = re.sub(pattern, '', output);
    # print(output.encode())
    for i in  re.findall(r"^\[(.*?)-(.*?)\] (.*?) (.*?)$", output, re.M):
        # print(i)
        image_name, section_name = i[3].split("`")
        if section_name == "__PAGEZERO":
            continue
        # print(image_name, section_name)
        file_path = os.path.join(DUMP_PATH, image_name)
        if not os.path.exists(file_path):
            os.mkdir(file_path)
        dumppath = os.path.join(file_path, section_name)
        cmd = "memory read --force -b --outfile {} {} {}".format(dumppath, i[0], i[1])
        # print(cmd)
        interpreter.HandleCommand(cmd, returnObject)
        output = returnObject.GetOutput();
        print(output)
        image_info[section_name] = {
            "address": i[0],
            "end_address": i[1],
            "size": i[2],
        }

    return image_info

def memdump(debugger, command, result, internal_dict):
    if not command:
        print(result, 'Please input the image name!')
        return
    info = {}
    if command == "alldump":
        images = get_images()
        if len(images):
            #如果找到了ASLR偏移，就设置断点
            for img in images:
                info[img] = dump_image(img)
    else:
        info[command] = dump_image(command)
        if len(info.items()) == 0:
            print("image dump error!")
            return

    json_path = os.path.join(DUMP_PATH, "images.json")
    with open(json_path, "w") as f:
        json.dump(info, f, indent = 2, separators=(',', ': '))
        print("memory dump:\n\tjson into: {}\n\tdump path: {}\n\timage count: {}".format(json_path, DUMP_PATH, len(info.keys())))

    # else:
        # print(result, 'images not found!')

# And the initialization code to add your commands 
def __lldb_init_module(debugger, internal_dict):
    # use: command script import ~/.lldb/memdump.py
    debugger.HandleCommand('command script add memdump -f memdump.memdump')
    print('The "memdump" python command has been installed and is ready for use.')
