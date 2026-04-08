def convert_background_to_jpg(background_url, file_path, get_path_of_temp_url):
    im = Image.open(file_path)
    out_im = file_path.replace('png', 'jpg')
    bg = Image.new('RGB', im.size, (255, 255, 255))
    bg.paste(im, (0, 0))
    bg.save(out_im, quality=55)
    return out_im
