import win32gui
import win32process
import win32con
import psutil
import sys


hwnds = []
def enumHandler(hwnd, hwnds):
    if win32gui.IsWindowVisible(hwnd):
        hwnds.append(hwnd)

win32gui.EnumWindows(enumHandler, hwnds)
i = 1
wins = [(hwnd, win32gui.GetWindowText(hwnd), win32process.GetWindowThreadProcessId(hwnd)[1]) for hwnd in hwnds if win32gui.GetWindowText(hwnd)]
list.sort(wins, key=lambda (_, _2, pid): psutil.Process(pid).name())
for (hwnd, wintext, pid) in wins:
    text = "[" + format(i, "2d") + "][" + psutil.Process(pid).name().split(".")[0] + "] "
    text += (20 - len(text)) * " " + wintext
    print text
    i += 1

num = int(sys.stdin.readline())
HWND = wins[num - 1][0]
win32gui.ShowWindow(HWND, win32con.SW_RESTORE)
win32gui.SetWindowPos(HWND,win32con.HWND_NOTOPMOST, 0, 0, 0, 0, win32con.SWP_NOMOVE + win32con.SWP_NOSIZE)
win32gui.SetWindowPos(HWND,win32con.HWND_TOPMOST, 0, 0, 0, 0, win32con.SWP_NOMOVE + win32con.SWP_NOSIZE)
win32gui.SetWindowPos(HWND,win32con.HWND_NOTOPMOST, 0, 0, 0, 0, win32con.SWP_SHOWWINDOW + win32con.SWP_NOMOVE + win32con.SWP_NOSIZE)
win32gui.SetActiveWindow(HWND)
win32gui.FlashWindow(HWND, 0)
#win32gui.ShowWindow(HWND, win32con.SW_RESTORE)
