from PIL import ImageDraw, ImageFont
import numpy as np
import colorsys

class RectangleDrawer:
    def __init__(self, font_path='arial.ttf', font_size=10):
        super().__init__()
        self.font_path = font_path
        self.font_size = font_size
        self.font = ImageFont.truetype(font=font_path,size=font_size)

    def draw_rectangle(self, image=None, box=[0,0,0,0], thickness=3,color=(0, 0, 0), text='', font_size=10):
        if text != '' and font_size != self.font_size:
            self.font = ImageFont.truetype(font=self.font_path,size=font_size)
            self.font_size = font_size

        top, left, bottom, right = box

        draw = ImageDraw.Draw(image)
        for i in range(thickness):
            draw.rectangle([left + i, top + i, right - i, bottom - i], outline=color)

        text_size = draw.textsize(text, self.font)
        text = text.encode('utf-8')
        if top - text_size[1] >= 0:
            text_origin = np.array([left, top - text_size[1]])
        else:
            text_origin = np.array([left, top + 1])
        draw.rectangle([tuple(text_origin), tuple(text_origin + text_size)], fill=color)
        draw.text(text_origin, str(text,'UTF-8'), fill=(0, 0, 0), font=self.font)
        del draw

        return image

def random_colors(number=0):
    hsv_tuples = [(x / number, 1., 1.) for x in range(number)]
    colors = list(map(lambda x: colorsys.hsv_to_rgb(*x), hsv_tuples))
    colors = list(map(lambda x: (int(x[0] * 255), int(x[1] * 255), int(x[2] * 255)), colors))
    return colors
        
