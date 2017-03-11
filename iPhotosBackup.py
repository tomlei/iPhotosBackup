#!/usr/bin/env python
#coding=utf8
# 将照片增量备份到指定目录, 并按照拍摄日期的月份分目录存放
# 按照年月分目录: 201602
# 文件统一重命名: 日期+时+分+序号(08_1423_00.JPG)


import os
import sys
import time
import shutil
import hashlib
from PIL import Image


SOURCE_DIR = ""      #iPhoto的Master路径
TARGET_DIR = ""      #备份的Samba路径
backup_index_file_name = "index"
sync_num = 0
repeat_num = 0
backup_index = ""
backup_index_fp = None

#获取图片EXIF中的创建时间
def get_create_datetime(image_path):
        try:
            img = Image.open(image_path)
            exifinfo = img._getexif()

            if 306 in exifinfo:
                #DateTime
                img_date = exifinfo[306]
                return "%s-%s-%s" % (img_date[:4], img_date[5:7], img_date[8:])
            elif 36867 in exifinfo:
                #DateTimeDigitized
                img_date = exifinfo[36867]
                return "%s-%s-%s" % (img_date[:4], img_date[5:7], img_date[8:])
            elif 36868 in exifinfo:
                #DateTimeOriginal
                img_date = exifinfo[36868]
                return "%s-%s-%s" % (img_date[:4], img_date[5:7], img_date[8:])
        except Exception as e:
            pass

        #File Crate DataTime
        print "Not DataTime. ", image_path.replace(SOURCE_DIR, "")
        state = os.stat(image_path)
        return time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(state[-2]))

#遍历所有iPhotos下面的照片
def recursion_source_file(dir_path):
    parents = os.listdir(dir_path)

    for parent in parents:
        child = os.path.join(dir_path, parent)
        
        if os.path.isdir(child):
            recursion_source_file(child)
        elif parent[0] != "." :
            sync_file(child)

def has_backup(hash_str):
    return backup_index.find(hash_str) != -1

#在备份索引文件中添加新记录
def backup_index_add(hash_str, dest_file):
    backup_index_fp.write(hash_str + "," + dest_file.replace(TARGET_DIR, "") + "\n")

def get_dest_file(dest_dir, create_datetime, extension):
    #日期+时+分+序号(08_1423_00.JPG)
    name_seq = 0
    dest_name = ""
    
    while True:
        dest_name = "%s_%s%s_%02d.%s" % (create_datetime[8:10], create_datetime[11:13], create_datetime[14:16], name_seq, extension)
        dest_file = os.path.join(dest_dir, dest_name)
        
        if os.path.exists(dest_file):
            name_seq += 1
        else:
            break

    return dest_file

#备份文件
def sync_file(source_file):
    global sync_num
    global repeat_num
    hash_str = get_hash_by_file(source_file)

    if not has_backup(hash_str):
        create_datetime = get_create_datetime(source_file).encode("utf8")
        dest_dir = os.path.join(TARGET_DIR, (create_datetime[:4] + create_datetime[5:7]))
        
        if not os.path.exists(dest_dir):
            os.mkdir(dest_dir)

        dest_file = get_dest_file(dest_dir, create_datetime, source_file.split(".")[-1])
        try:
            shutil.copyfile(source_file, dest_file)
        except Exception as e:
            print source_file, dest_file
        backup_index_add(hash_str, dest_file)
        sync_num += 1
    else:
        repeat_num += 1

def get_hash_by_file(file_path):
    m = hashlib.sha1()

    with open(file_path, 'r') as f:
        while True:
            data = f.read(10240)
            if not data:
                break
            m.update(data)

    return m.hexdigest()

#递归备份文件
def recursion_reindex_photo(index_fp, dir_path):
    parents = os.listdir(dir_path)

    for parent in parents:
        child = os.path.join(dir_path, parent)

        if os.path.isdir(child):
            recursion_reindex_photo(index_fp, child)
        elif parent[0] != ".":
            hash_str = get_hash_by_file(child)
            index_fp.write(hash_str + "," + child.replace(TARGET_DIR, "") + "\n")

def init_backup_index():
    global backup_index
    global backup_index_fp

    backup_index_file = os.path.join(TARGET_DIR, backup_index_file_name)

    if os.path.exists(backup_index_file):
        with open(backup_index_file, "r") as backup_index_fp:
            backup_index = backup_index_fp.read()

    backup_index_fp = open(backup_index_file, "a")

#重建索引
def reindex_photo():
    with open("index", "w") as fp:
        recursion_reindex_photo(fp, TARGET_DIR);

def backup_photo():
    #try:
    init_backup_index()
    recursion_source_file(SOURCE_DIR)
    #except Exception as e:
    #    print "Sync error."
    
    backup_index_fp.close()
    print "Sync: %s, Repeat: %s" % (sync_num, repeat_num)

if __name__ == '__main__':
    if len(sys.argv) == 2 and sys.argv[1] == "reindex":
        reindex_photo()
    else:
        backup_photo()

