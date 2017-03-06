#coding=utf8
#将iPhotos下面的照片增量备份到指定目录, 并按照拍摄日期的月份分目录存放
#例如: 201701/IMG_2222.JPG


import os
import sys
import time
import shutil
from PIL import Image


#iPhoto的Master路径
iphoto_path = "/Users/tomlei/Pictures/照片图库.photoslibrary/Masters"

#备份的Samba路径
samba_path = "/Volumes/共享/照片/000000_iPhotos"


#获取图片EXIF创建时间
def get_exif_datetime(image_path):
    try:
        img = Image.open(image_path)
        exifinfo = img._getexif()
        img_date = exifinfo[CREATE_DATE]

        return "%s-%s-%s" % (img_date[:4], img_date[5:7], img_date[8:])
    except Exception, e:
        state = os.stat(image_path)
        return time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(state[-2]))

#遍历所有iPhotos下面的照片
def recursive_file(map_fp, dir_path):
    parents = os.listdir(dir_path)

    for parent in parents:
        child = os.path.join(dir_path, parent)
        
        if os.path.isdir(child):
            recursive_file(map_fp, child)
        else:
            file_date = get_exif_datetime(child)
            dest_file = os.path.join(file_date[:4] + file_date[5:7], parent)
            map_fp.write(dest_file + "," + child + "\n")

#备份文件
def sync_file():
    sync_file_num = 0

    with open("map_file", "r") as map_fp:
        for line in map_fp:
            (dest_file, source_file) = line[:-1].split(",")
            dest_path = os.path.join(samba_path, dest_file[:6])
            dest_file = os.path.join(samba_path, dest_file)
            
            if not os.path.exists(dest_path):
                os.mkdir(dest_path)
            elif os.path.isfile(dest_file):
                continue

            shutil.copyfile(source_file, dest_file)
            sync_file_num += 1

    print "Sync File:", sync_file_num

if __name__ == '__main__':

    with open("map_file", "w") as map_fp:
        recursive_file(map_fp, iphoto_path)

    sync_file()
    os.remove("map_file")

