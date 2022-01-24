import pyautogui
import time
import keyboard

# def main():
#     keyboard.press_and_release('up')
#     for i in range(130):
#         keyboard.press_and_release('backspace')
#     for i in range(130):
#         keyboard.press_and_release('right')

# time.sleep(5)
# for i in range(100):
#     main()

cacti = [215, 380, 260, 345]
birb = []

for i in range(cacti[0], cacti[2]):
    print(i)
    for j in range(cacti[1], cacti[3]):
        print(i, j)
def main():
    #get color of cacti
    # color = pyautogui.pixel(cacti[0], cacti[1])
    # color = list(color)
    # if color == [83, 83, 83]:
    #     keyboard.press_and_release('space')
    color = pyautogui.pixel(215, 380)
    print(color)
    if color == (83, 83, 83):
        keyboard.press_and_release('space')
    
while True:
    main()