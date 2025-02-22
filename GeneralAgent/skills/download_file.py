
def download_file(file_url, save_path):
    """download file to save_path, return True if success, else False"""
    """实现一个下载文件的函数，返回文件路径"""
    import requests
    import logging
    try:
        response = requests.get(file_url)
        with open(save_path, "wb") as f:
            f.write(response.content)
        # print("Success: 文件(%s)已下载至 %s" % (file_url, save_path))
        return True
    except Exception as e:
        # print("Error: 文件下载失败:", e)
        logging.error(e)
        return False


def try_download_file(file_path):
    import os
    from GeneralAgent import skills
    from PIL import Image
    """Try to download file if it is a url, else return file_path"""
    if file_path.startswith("http://") or file_path.startswith("https://"):
        save_path = skills.unique_name() + '.' + file_path.split('.')[-1]
        success = skills.download_file(file_path, save_path)
        if success:
            if save_path.endswith('.png') or save_path.endswith('.PNG'):
                # 转成jpg
                png_image = Image.open(save_path)
                jpg_save_path = skills.unique_name() + '.jpg'
                png_image.save(jpg_save_path, 'JPEG')
                os.remove(save_path)
                return jpg_save_path
            else:
                return save_path
        else:
            return file_path
    else:
        return file_path

if __name__ == '__main__':
    # download_file('https://ai.tongtianta.site/file-upload/gvsAc4cEm543iaX5x/5.pdf', '1.pdf')
    download_file('https://ai.tongtianta.site/file-upload/27XEb3WgyDru5eFFe/9.pdf', '3.pdf')