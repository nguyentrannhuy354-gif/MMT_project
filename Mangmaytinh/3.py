import pyautogui #dieu khien chuot,ban phim va chup anh man hinh
import io 

def take_screenshot():
    screenshot = pyautogui.screenshot()
    img_byte_arr = io.byteIO()
    screenshot.save(img_byte_arr, format ="PNG")
    print("đã chụp và lưu ảnh thành công")
    return img_byte_arr.getvalue()
